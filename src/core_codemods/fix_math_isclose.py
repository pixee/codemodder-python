import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
    NewArg,
)
from codemodder.codemods.utils import is_zero
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class FixMathIsCloseTransformer(
    LibcstResultTransformer,
    NameAndAncestorResolutionMixin,
):
    change_description = "Add `abs_tol` to `math.isclose` call"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if (
            not self.node_is_selected(original_node)
            or self.find_base_name(original_node.func) != "math.isclose"
            or len(original_node.args) < 2
        ):
            return updated_node

        if self.at_least_one_zero_arg(original_node.args):
            for arg in original_node.args[2:]:
                match arg:
                    case cst.Arg(keyword=cst.Name(value="abs_tol")) as matched_arg:
                        # A `abs_tol` kwarg set to not 0 is acceptable if comparing to 0
                        if not is_zero(matched_arg.value):
                            return updated_node

            new_args = self.replace_args(
                original_node,
                [NewArg(name="abs_tol", value="1e-09", add_if_missing=True)],
            )

            self.report_change(original_node)
            return self.update_arg_target(updated_node, new_args)

        return updated_node

    def at_least_one_zero_arg(self, original_args: list[cst.Arg]):
        first_arg = self.resolve_expression(original_args[0].value)
        second_arg = self.resolve_expression(original_args[1].value)
        return is_zero(first_arg) or is_zero(second_arg)


FixMathIsClose = CoreCodemod(
    metadata=Metadata(
        name="fix-math-isclose",
        summary="Add `abs_tol` to `math.isclose` Call",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(url="https://docs.python.org/3/library/math.html#math.isclose"),
        ],
    ),
    transformer=LibcstTransformerPipeline(FixMathIsCloseTransformer),
    detector=None,
)
