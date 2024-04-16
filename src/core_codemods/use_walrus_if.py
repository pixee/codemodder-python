import itertools
from collections import namedtuple
from typing import List, Optional, Tuple

import libcst as cst
from libcst._position import CodeRange
from libcst.metadata import ParentNodeProvider, ScopeProvider

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod

FoundAssign = namedtuple("FoundAssign", ["assign", "target", "value"])


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class UseWalrusIf(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="use-walrus-if",
        summary="Use Assignment Expression (Walrus) In Conditional",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/whatsnew/3.8.html#assignment-expressions"
            ),
        ],
    )
    change_description = (
        "Replaces multiple expressions involving `if` operator with 'walrus' operator."
    )
    METADATA_DEPENDENCIES = (
        *SimpleCodemod.METADATA_DEPENDENCIES,
        ParentNodeProvider,
        ScopeProvider,
    )

    _modify_next_if: List[Tuple[CodeRange, cst.NamedExpr]]
    _if_stack: List[Optional[Tuple[CodeRange, cst.NamedExpr]]]
    assigns: dict[cst.Assign, cst.NamedExpr]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._modify_next_if = []
        self._if_stack = []
        self.assigns = {}

    def _build_named_expr(self, target, value, parens=True):
        return cst.NamedExpr(
            target=target,
            value=value,
            lpar=[cst.LeftParen()] if parens else [],
            rpar=[cst.RightParen()] if parens else [],
        )

    def _filter_assigns(self, node: cst.CSTNode) -> FoundAssign | None:
        match node:
            case cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(target=cst.Name() as target),
                        ],
                        value=value,
                    ) as assign
                ]
            ):
                return FoundAssign(assign, target, value)
        return None

    def _filter_if(self, node: cst.CSTNode) -> cst.BaseExpression | None:
        match node:
            case cst.If(test=test):
                return test
        return None

    def _single_access(self, original_node: cst.IfExp) -> bool:
        match original_node.test:
            case cst.Name():
                access = self.find_accesses(original_node.test)
            case cst.UnaryOperation():
                access = self.find_accesses(original_node.test.expression)
            case _:
                access = self.find_accesses(original_node.test.left)
        return len(access) == 1

    def on_visit(self, node: cst.CSTNode) -> Optional[bool]:
        if len(node.children) < 2:
            return super().on_visit(node)

        for a, b in pairwise(node.children):
            if not (found_assign := self._filter_assigns(a)):
                continue
            if not (if_test := self._filter_if(b)):
                continue

            assign, target, value = found_assign
            match if_test:
                # If test can be a comparison expression
                case cst.Comparison(
                    left=cst.Name() as left,
                    comparisons=[
                        cst.ComparisonTarget(
                            operator=(
                                cst.Is() | cst.IsNot() | cst.Equal() | cst.NotEqual()
                            )
                        )
                    ],
                ):

                    if left.value == target.value:
                        named_expr = self._build_named_expr(target, value, parens=True)
                        self.assigns[assign] = named_expr
                case cst.Name() as name:
                    # If test can also be a bare name
                    if name.value == target.value:
                        named_expr = self._build_named_expr(target, value, parens=False)
                        self.assigns[assign] = named_expr
                case cst.UnaryOperation(
                    operator=cst.Not(), expression=cst.Name() as name
                ):
                    if name.value == target.value:
                        named_expr = self._build_named_expr(target, value, parens=True)
                        self.assigns[assign] = named_expr
        return super().on_visit(node)

    def visit_If(self, node: cst.If):
        del node
        self._if_stack.append(
            self._modify_next_if.pop() if len(self._modify_next_if) else None
        )

    def leave_If(self, original_node, updated_node):
        # TODO: add filter by include or exclude that works for nodes
        # that that have different start/end numbers.

        if (result := self._if_stack.pop()) is not None:
            position, named_expr = result
            self.add_change_from_position(position, self.change_description)

            # If a variable has a single access, it means it's only assigned and not used again.
            # In this case, do not use a walrus named expr to prevent unused variable warnings.
            # Instead, move the variable's rhs directly into the if statement.
            new_expression = (
                named_expr.value if self._single_access(original_node) else named_expr
            )

            match updated_node.test:
                case cst.Name():
                    return updated_node.with_changes(test=new_expression)
                case cst.UnaryOperation():
                    return updated_node.with_changes(
                        test=updated_node.test.with_changes(expression=new_expression)
                    )
                case _:
                    return updated_node.with_changes(
                        test=updated_node.test.with_changes(left=new_expression)
                    )

        return original_node

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign):
        del updated_node
        if named_expr := self.assigns.get(original_node):
            position = self.node_position(original_node)
            self._modify_next_if.append((position, named_expr))
            return cst.RemoveFromParent()

        return original_node

    def leave_SimpleStatementLine(self, original_node, updated_node):
        """
        Preserves the whitespace and comments in the line when all children are removed.

        This feels like a bug in libCST but we'll work around it for now.
        """
        if not updated_node.body:
            trailing_whitespace = (
                (
                    original_node.trailing_whitespace.with_changes(
                        whitespace=cst.SimpleWhitespace(""),
                    ),
                )
                if original_node.trailing_whitespace.comment
                else ()
            )
            # NOTE: The effect of this is to preserve the
            # whitespace and comments. However, the type expected by
            # cst.Module.body is Sequence[Union[SimpleStatementLine, BaseCompoundStatement]].
            # So technically this violates the expected return type since we
            # are not adding a new SimpleStatementLine but instead just bare
            # EmptyLine and Comment nodes.
            # A more correct solution would involve transferring any whitespace
            # and comments to the subsequent SimpleStatementLine (which
            # contains the If statement), but this would require a lot more
            # state management to fit within the visitor pattern. We should
            # revisit this at some point later.
            return cst.FlattenSentinel(
                tuple(original_node.leading_lines) + trailing_whitespace
            )

        return updated_node
