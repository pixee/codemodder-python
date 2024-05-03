import libcst as cst
from libcst import matchers as m

from core_codemods.api import Metadata, ReviewGuidance

from .combine_calls_base import CombineCallsBaseCodemod


class CombineStartswithEndswith(CombineCallsBaseCodemod):
    metadata = Metadata(
        name="combine-startswith-endswith",
        summary="Simplify Boolean Expressions Using `startswith` and `endswith`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Use tuple of matches instead of boolean expression"

    combinable_funcs = ["startswith", "endswith"]
    dedupilcation_attr = "evaluated_value"
    args_to_combine = [0]
    args_to_keep_as_is = []

    def make_call_matcher(self, func_name: str) -> m.Call:
        return m.Call(
            func=m.Attribute(value=m.Name(), attr=m.Name(func_name)),
            args=[
                m.Arg(
                    value=m.Tuple()
                    | m.SimpleString()
                    | m.ConcatenatedString()
                    | m.FormattedString()
                    | m.Name()
                )
            ],
        )

    def check_calls_same_instance(
        self, left_call: cst.Call, right_call: cst.Call
    ) -> bool:
        return left_call.func.value.value == right_call.func.value.value
