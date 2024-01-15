import libcst as cst
from typing import Union
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin, AncestorPatternsMixin


class FixEmptySequenceComparison(
    BaseCodemod, NameResolutionMixin, AncestorPatternsMixin
):
    NAME = "fix-empty-sequence-comparison"
    SUMMARY = "TODO"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "TODO"
    REFERENCES: list = []

    def leave_Comparison(
        self, original_node: cst.Comparison, updated_node: cst.Comparison
    ):
        del updated_node
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return original_node

        maybe_parent = self.get_parent(original_node)

        match original_node:
            case cst.Comparison(
                left=left, comparisons=[cst.ComparisonTarget() as target]
            ):
                if isinstance(target.operator, cst.Equal | cst.NotEqual):
                    right = target.comparator
                    # right is empty: x == []
                    # left is empty: [] == x
                    if (
                        empty_left := self._is_empty_sequence(left)
                    ) or self._is_empty_sequence(right):
                        self.report_change(original_node)
                        comp_var = right if empty_left else left
                        match maybe_parent:
                            case cst.If() | cst.Assert():
                                return (
                                    comp_var
                                    if isinstance(target.operator, cst.NotEqual)
                                    else cst.UnaryOperation(
                                        operator=cst.Not(),
                                        expression=comp_var,
                                    )
                                )
                            case _:
                                return (
                                    cst.parse_expression(f"bool({comp_var.value})")
                                    if isinstance(target.operator, cst.NotEqual)
                                    else cst.UnaryOperation(
                                        operator=cst.Not(),
                                        expression=comp_var,
                                    )
                                )

        return original_node

    def _is_empty_sequence(self, node: cst.BaseExpression):
        match node:
            case cst.List(elements=[]) | cst.Dict(elements=[]) | cst.Tuple(elements=[]):
                return True
        return False
