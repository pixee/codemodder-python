import libcst as cst
from libcst import UnaryOperation
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance

from codemodder.codemods.utils_mixin import NameResolutionMixin


class NumpyNanEquality(BaseCodemod, NameResolutionMixin):
    NAME = "numpy-nan-equality"
    SUMMARY = "Replace == comparison with numpy.isnan()"
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

    # pylint: disable-next=too-many-arguments
    def _build_nan_comparison(
        self, nan_node, node, preprend_not, lpar, rpar
    ) -> cst.BaseExpression:
        if maybe_numpy_alias := self.find_alias_for_import_in_node("numpy", nan_node):
            call = cst.parse_expression(f"{maybe_numpy_alias}.isnan()")
        else:
            self.add_needed_import("numpy")
            self.remove_unused_import(nan_node)
            call = cst.parse_expression("numpy.isnan()")
        call = call.with_changes(args=[cst.Arg(value=node)])
        if preprend_not:
            return UnaryOperation(
                operator=cst.Not(), expression=call, lpar=lpar, rpar=rpar
            )
        return call.with_changes(lpar=lpar, rpar=rpar)

    def _is_np_nan_eq(self, left: cst.BaseExpression, target: cst.ComparisonTarget):
        if isinstance(target.operator, cst.Equal | cst.NotEqual):
            right = target.comparator
            left_name = self.find_base_name(left)
            right_name = self.find_base_name(right)
            if self.np_nan == left_name:
                return left, right
            if self.np_nan == right_name:
                return right, left
        return None

    def leave_Comparison(
        self, original_node: cst.Comparison, updated_node: cst.Comparison
    ) -> cst.BaseExpression:
        if self.filter_by_path_includes_or_excludes(self.node_position(original_node)):
            match original_node:
                case cst.Comparison(comparisons=[cst.ComparisonTarget() as target]):
                    maybe_nan_eq = self._is_np_nan_eq(original_node.left, target)
                    if maybe_nan_eq:
                        nan_node, node = maybe_nan_eq
                        self.report_change(original_node)
                        return self._build_nan_comparison(
                            nan_node,
                            node,
                            isinstance(target.operator, cst.NotEqual),
                            lpar=original_node.lpar,
                            rpar=original_node.rpar,
                        )
        return updated_node
