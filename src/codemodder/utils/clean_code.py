import itertools
from typing import Union

import libcst as cst
from libcst.codemod import (
    Codemod,
    CodemodContext,
    ContextAwareTransformer,
    ContextAwareVisitor,
    VisitorBasedCodemodCommand,
)
from libcst.metadata import ClassScope, GlobalScope, ParentNodeProvider, ScopeProvider

from codemodder.codemods.utils import ReplacementNodeType, ReplaceNodes
from codemodder.codemods.utils_mixin import (
    NameAndAncestorResolutionMixin,
    NameResolutionMixin,
)
from codemodder.utils.format_string_parser import (
    PrintfStringExpression,
    PrintfStringText,
    dict_to_values_dict,
    expressions_from_replacements,
    parse_formatted_string,
)
from codemodder.utils.linearize_string_expression import LinearizeStringMixin
from codemodder.utils.utils import is_empty_sequence_literal, is_empty_string_literal


class RemoveEmptyExpressionsFormatting(Codemod):
    """
    Cleans and removes string format operator (i.e. `%`) expressions that formats empty expressions or strings. For example, `"abc%s123" % ""` -> `"abc123"`, or `"abc" % {}` -> `"abc"`.
    """

    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        ScopeProvider,
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        result = tree
        visitor = RemoveEmptyExpressionsFormattingVisitor(self.context)
        result.visit(visitor)
        if visitor.node_replacements:
            result = result.visit(ReplaceNodes(visitor.node_replacements))
        return result

    def should_allow_multiple_passes(self) -> bool:
        return True


class RemoveEmptyExpressionsFormattingVisitor(
    ContextAwareVisitor, NameAndAncestorResolutionMixin, LinearizeStringMixin
):

    def __init__(self, context: CodemodContext) -> None:
        self.node_replacements: dict[cst.CSTNode, ReplacementNodeType] = {}
        super().__init__(context)

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

    def _build_replacements(self, node, node_parts, parts_to_remove):
        new_raw_value = ""
        change = False
        for part in node_parts:
            if part in parts_to_remove:
                change = True
            else:
                new_raw_value += part.value
        if change:
            match node:
                case cst.SimpleString():
                    self.node_replacements[node] = node.with_changes(
                        value=node.prefix + node.quote + new_raw_value + node.quote
                    )
                case cst.FormattedStringText():
                    self.node_replacements[node] = node.with_changes(
                        value=new_raw_value
                    )

    def _record_node_pieces(self, parts) -> dict:
        node_pieces: dict[
            cst.CSTNode,
            list[PrintfStringExpression | PrintfStringText],
        ] = {}
        for part in parts:
            match part:
                case PrintfStringText() | PrintfStringExpression():
                    if part.origin in node_pieces:
                        node_pieces[part.origin].append(part)
                    else:
                        node_pieces[part.origin] = [part]
        return node_pieces

    def leave_BinaryOperation(self, original_node: cst.BinaryOperation):
        if not isinstance(original_node.operator, cst.Modulo):
            return

        # is left or right an empty literal?
        if is_empty_string_literal(self.resolve_expression(original_node.left)):
            self.node_replacements[original_node] = cst.SimpleString("''")
            return
        right = self.resolve_expression(right := original_node.right)
        if is_empty_sequence_literal(right):
            self.node_replacements[original_node] = original_node.left
            return

        # gather all the parts of the format operator
        resolved_dict = {}
        match right:
            case cst.Dict():
                resolved_dict = self._resolve_dict(right)
                keys: dict | list = dict_to_values_dict(resolved_dict)
            case _:
                keys = expressions_from_replacements(right)
        linearized_string_expr = self.linearize_string_expression(original_node.left)
        parsed = parse_formatted_string(
            linearized_string_expr.parts if linearized_string_expr else [], keys
        )
        node_pieces = self._record_node_pieces(parsed)

        # failed parsing of expression, aborting
        if not parsed:
            return

        # is there any expressions to replace? if not, remove the operator
        if all(not isinstance(p, PrintfStringExpression) for p in parsed):
            self.node_replacements[original_node] = original_node.left
            return

        # gather all the expressions parts that resolves to an empty string and remove them
        to_remove = set()
        for part in parsed:
            match part:
                case PrintfStringExpression():
                    resolved_part_expression = self.resolve_expression(part.expression)
                    if is_empty_string_literal(resolved_part_expression):
                        to_remove.add(part)
        keys_to_remove = {part.key or 0 for part in to_remove}
        for part in to_remove:
            self._build_replacements(part.origin, node_pieces[part.origin], to_remove)

        # remove all the elements on the right that resolves to an empty string
        match right:
            case cst.Dict():
                for v in resolved_dict.values():
                    resolved_v = self.resolve_expression(v)
                    if is_empty_string_literal(resolved_v):
                        parent = self.get_parent(v)
                        if parent:
                            self.node_replacements[parent] = cst.RemovalSentinel.REMOVE

            case cst.Tuple():
                new_tuple_elements = []
                # outright remove
                if len(keys_to_remove) != len(keys):
                    for i, element in enumerate(right.elements):
                        if i not in keys_to_remove:
                            new_tuple_elements.append(element)
                if len(new_tuple_elements) != len(right.elements):
                    if len(new_tuple_elements) == 1:
                        self.node_replacements[right] = new_tuple_elements[0].value
                    else:
                        self.node_replacements[right] = right.with_changes(
                            elements=new_tuple_elements
                        )
            case _:
                if keys_to_remove:
                    self.node_replacements[original_node] = self.node_replacements.get(
                        original_node.left, original_node.left
                    )


class RemoveUnusedVariables(VisitorBasedCodemodCommand, NameResolutionMixin):
    """
    Removes assinments that aren't referenced anywhere else. It will preseve assignments that are in exposed scopes, that is, module or class scope.
    """

    def _handle_target(self, node):
        # TODO starred elements
        # TODO list/tuple case, remove assignment values
        match node:
            # case cst.Tuple() | cst.List():
            #    new_elements = []
            #    for e in node.elements:
            #        new_expr = self._handle_target(e.value)
            #        if new_expr:
            #            new_elements.append(e.with_changes(value = new_expr))
            #    if new_elements:
            #        if len(new_elements) ==1:
            #            return new_elements[0]
            #        return node.with_changes(elements = new_elements)
            #    return None
            case cst.Name():
                if self.find_accesses(node):
                    return node
                else:
                    return None
            case _:
                return node

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
        if scope := self.get_metadata(ScopeProvider, original_node, None):
            if isinstance(scope, GlobalScope | ClassScope):
                return updated_node

        new_targets = []
        for target in original_node.targets:
            if new_target := self._handle_target(target.target):
                new_targets.append(target.with_changes(target=new_target))
        # remove everything
        if not new_targets:
            return cst.RemovalSentinel.REMOVE
        return updated_node.with_changes(targets=new_targets)


class NormalizeFStrings(ContextAwareTransformer):
    """
    Finds all the f-strings whose parts are only composed of FormattedStringText and concats all of them in a single part.
    """

    def leave_FormattedString(
        self, original_node: cst.FormattedString, updated_node: cst.FormattedString
    ) -> cst.BaseExpression:
        all_parts = list(
            itertools.takewhile(
                lambda x: isinstance(x, cst.FormattedStringText), original_node.parts
            )
        )
        if len(all_parts) != len(updated_node.parts):
            return updated_node
        new_part = cst.FormattedStringText(
            value="".join(map(lambda x: x.value, all_parts))
        )
        return updated_node.with_changes(parts=[new_part])
