from dataclasses import dataclass
from typing import ClassVar, Collection, Optional

import libcst as cst
from libcst import matchers
from libcst.codemod import CodemodContext, ContextAwareVisitor
from libcst.metadata import ParentNodeProvider, ProviderT, ScopeProvider

from codemodder.codemods.utils import BaseType, infer_expression_type
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.utils.format_string_parser import (
    ExpressionNodeType,
    PrintfStringExpression,
    PrintfStringText,
    StringLiteralNodeType,
    dict_to_values_dict,
    expressions_from_replacements,
    parse_formatted_string,
)


@dataclass
class LinearizedStringExpression:
    """
    An string expression broken into several pieces that composes it.
    :ivar parts: Contains all the parts that composes an string expression in order.
    :ivar node_pieces: If a string literal was broken into several pieces by the presence of a format operator, this dict maps the literal into its pieces.
    """

    parts: list[StringLiteralNodeType | ExpressionNodeType]
    node_pieces: dict[
        cst.SimpleString | cst.FormattedStringText,
        list[PrintfStringText | PrintfStringExpression],
    ]
    # TODO crutch, maybe maintain the whole tree?
    aliased: dict[StringLiteralNodeType | ExpressionNodeType, cst.Name]


class LinearizeStringMixin(cst.MetadataDependent):

    METADATA_DEPENDENCIES: ClassVar[Collection[ProviderT]] = (
        ParentNodeProvider,
        ScopeProvider,
    )
    """
    A mixin class for libcst Codemod classes. It provides a method to gather all the pieces that composes a string expression.
    """

    context: CodemodContext

    def linearize_string_expression(
        self, expr: cst.BaseExpression
    ) -> Optional[LinearizedStringExpression]:
        """
        Linearizes a string expression. By linearization it means that if a string expression is the concatenation of several string literals and expressions, it returns all the expressions in order of concatenation. For example, in the following:
        ```python
        def foo(argument, expression):
            b = "'" + argument + "'"
            a = f"text{expression}"
            string = a + b + " end"
            print(string)
        ```
        The expression `string` in `print(string)` can be linearized into the following parts: "text", expression, "'", argument, "'", "end". The returned object will contain the libcst nodes that represent all the pieces in order.
        """
        visitor = LinearizeStringExpressionVisitor(self.context)
        expr.visit(visitor)
        if visitor.leaves:
            return LinearizedStringExpression(
                visitor.leaves,
                visitor.node_pieces,
                visitor.aliased,
            )
        return None


class LinearizeStringExpressionVisitor(
    ContextAwareVisitor, NameAndAncestorResolutionMixin
):
    """
    Gather all the expressions that are concatenated to build the query.
    """

    def __init__(self, context) -> None:
        self.tree = None
        self.leaves: list[StringLiteralNodeType | ExpressionNodeType] = []
        self.aliased: dict[StringLiteralNodeType | ExpressionNodeType, cst.Name] = {}
        self.node_pieces: dict[
            cst.SimpleString | cst.FormattedStringText,
            list[PrintfStringText | PrintfStringExpression],
        ] = {}
        super().__init__(context)

    def _record_node_pieces(self, parts):
        for part in parts:
            match part:
                case PrintfStringText() | PrintfStringExpression():
                    if part.origin in self.node_pieces:
                        self.node_pieces[part.origin].append(part)
                    else:
                        self.node_pieces[part.origin] = [part]

    def on_visit(self, node: cst.CSTNode):
        # We only care about expressions, ignore everything else
        # Mostly as a sanity check, this may not be necessary since we start the visit with an expression node
        if isinstance(
            node,
            (
                cst.BaseExpression,
                cst.FormattedStringExpression,
                cst.FormattedStringText,
            ),
        ):
            # These will be the only types that will be properly visited
            if not matchers.matches(
                node,
                matchers.Name()
                | matchers.FormattedString()
                | matchers.BinaryOperation()
                | matchers.FormattedStringExpression()
                | matchers.ConcatenatedString(),
            ):
                self.leaves.append(node)
            else:
                return super().on_visit(node)
        return False

    def _resolve_dict(
        self, dict_node: cst.Dict
    ) -> dict[cst.BaseExpression, cst.BaseExpression]:
        returned: dict[cst.BaseExpression, cst.BaseExpression] = {}
        for element in dict_node.elements:
            match element:
                case cst.DictElement():
                    returned |= {element.key: element.value}
                case cst.StarredDictElement():
                    resolved = self.resolve_expression(element.value)
                    if isinstance(resolved, cst.Dict):
                        returned |= self._resolve_dict(resolved)
        return returned

    def visit_FormatLiteralStringExpression(self, pfse: PrintfStringExpression):
        visitor = LinearizeStringExpressionVisitor(self.context)
        pfse.expression.visit(visitor)

        self.leaves.extend(visitor.leaves)
        self.aliased |= visitor.aliased
        self.node_pieces |= visitor.node_pieces

    def visit_BinaryOperation(self, node: cst.BinaryOperation) -> Optional[bool]:
        maybe_type = infer_expression_type(node)
        if not maybe_type or maybe_type == BaseType.STRING:
            match node.operator:
                case cst.Modulo():
                    visitor = LinearizeStringExpressionVisitor(self.context)
                    node.left.visit(visitor)
                    resolved = self.resolve_expression(node.right)
                    parsed = None
                    match resolved:
                        case cst.Dict():
                            keys: dict | list = dict_to_values_dict(
                                self._resolve_dict(resolved)
                            )
                        case cst.Tuple():
                            keys = expressions_from_replacements(resolved)
                        case _:
                            keys = expressions_from_replacements(node.right)
                    parsed = parse_formatted_string(visitor.leaves, keys)
                    self._record_node_pieces(parsed)
                    # something went wrong, abort
                    if not parsed:
                        self.leaves.append(node)
                        return False
                    for piece in parsed:
                        match piece:
                            case PrintfStringExpression():
                                self.visit_FormatLiteralStringExpression(piece)
                            case _:
                                self.leaves.append(piece)
                    self.aliased |= visitor.aliased
                    self.node_pieces |= visitor.node_pieces
                    return False
                case cst.Add():
                    return True
        self.leaves.append(node)
        return False

    # recursive search
    def visit_Name(self, node: cst.Name) -> Optional[bool]:
        self.leaves.extend(self.recurse_Name(node))
        return False

    def visit_Attribute(self, node: cst.Attribute) -> Optional[bool]:
        # TODO should we also try to resolve values for attributes?
        self.leaves.append(node)
        return False

    def recurse_Name(
        self, node: cst.Name
    ) -> list[StringLiteralNodeType | ExpressionNodeType]:
        # if the expression is a name, try to find its single assignment
        if (resolved := self.resolve_expression(node)) != node:
            visitor = LinearizeStringExpressionVisitor(self.context)
            resolved.visit(visitor)
            if len(visitor.leaves) == 1:
                self.aliased[visitor.leaves[0]] = node
                return visitor.leaves
            self.aliased |= visitor.aliased
            self.node_pieces |= visitor.node_pieces
            return visitor.leaves
        return [node]
