from collections import namedtuple
from typing import Optional
import libcst as cst
from libcst import matchers
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance

from codemodder.codemods.utils_mixin import NameResolutionMixin

NodeWithTrueName = namedtuple("NodeWithTrueName", ["node", "name"])


class NumpyNanEquality(BaseCodemod, NameResolutionMixin):
    NAME = "numpy-nan-equality"
    SUMMARY = "Uses numpy.isnan() instead of ==."
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = SUMMARY
    REFERENCES = [
        {
            "url": "https://numpy.org/doc/stable/reference/constants.html#numpy.nan",
            "description": "",
        },
    ]
    CHANGE_DESCRIPTION = "Replaces == check with numpy.isnan()."

    np_nan = "numpy.nan"

    def _is_np_nan(
        self, left: NodeWithTrueName, right: NodeWithTrueName
    ) -> Optional[tuple[cst.CSTNode, cst.CSTNode]]:
        if self.np_nan == left.name:
            return left.node, right.node
        if self.np_nan == right.name:
            return right.node, left.node
        return None

    def _build_conjunction(
        self, expressions: list[cst.BaseExpression], index: int
    ) -> cst.BaseExpression:
        if index == 0:
            return expressions[0]
        return cst.BooleanOperation(
            left=self._build_conjunction(expressions, index - 1),
            right=expressions[index],
            operator=cst.And(),
        )

    def _build_new_comparison(self, expression_triples) -> cst.BaseExpression:
        conjunction_expression = []
        before: Optional[cst.Comparison] = None
        for left, right, operator in expression_triples:
            maybe_has_nan = self._is_np_nan(left, right)
            if maybe_has_nan:
                nan_node, node = maybe_has_nan
                if before:
                    conjunction_expression.append(before)
                    before = None
                conjunction_expression.append(
                    self._build_nan_comparison(nan_node, node)
                )
            else:
                if before:
                    before.comparisons.append(
                        cst.ComparisonTarget(operator=operator, comparator=right.node)
                    )
                else:
                    before = cst.Comparison(
                        left=left.node,
                        comparisons=[
                            cst.ComparisonTarget(
                                operator=operator, comparator=right.node
                            )
                        ],
                    )
        if before:
            conjunction_expression.append(before)
        return self._build_conjunction(
            conjunction_expression, len(conjunction_expression) - 1
        )

    def _break_into_triples(self, comparison: cst.Comparison):
        """
        Breaks a comparison expression into triples.
        For example, the expression a == b == c is equivalent to a == b and b == c. This method will break it into [(a,b,==), (b,c,==)].
        """
        left = NodeWithTrueName(
            node=comparison.left, name=self.find_base_name(comparison.left)
        )
        # the first always exists
        ct = comparison.comparisons[0]
        right = NodeWithTrueName(ct.comparator, self.find_base_name(ct.comparator))
        triples = [(left, right, ct.operator)]
        for ct in comparison.comparisons[1:]:
            left = right
            right = NodeWithTrueName(ct.comparator, self.find_base_name(ct.comparator))
            triples.append((left, right, ct.operator))
        return triples

    def _build_nan_comparison(self, nan_node, node):
        maybe_numpy_alias = self.find_alias_for_import_in_node("numpy", nan_node)
        if maybe_numpy_alias:
            call = cst.parse_expression(f"{maybe_numpy_alias}.isnan()")
        else:
            self.add_needed_import("numpy")
            call = cst.parse_expression("numpy.isnan()")
        return call.with_changes(args=[cst.Arg(value=node)])

    def leave_Comparison(
        self, original_node: cst.Comparison, updated_node: cst.Comparison
    ) -> cst.BaseExpression:
        if self.filter_by_path_includes_or_excludes(self.node_position(original_node)):
            comparison_triples = self._break_into_triples(original_node)
            for left, right, operator in comparison_triples:
                if matchers.matches(operator, matchers.Equal()) and self.np_nan in (
                    left.name,
                    right.name,
                ):
                    self.report_change(original_node)
                    return self._build_new_comparison(comparison_triples)
        return updated_node
