import libcst as cst
from libcst import matchers as m

from core_codemods.api import Metadata, ReviewGuidance

from .combine_calls_base import CombineCallsBaseCodemod


class CombineIsinstanceIssubclass(CombineCallsBaseCodemod):
    metadata = Metadata(
        name="combine-isinstance-issubclass",
        summary="Simplify Boolean Expressions Using `isinstance` and `issubclass`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Use tuple of matches instead of boolean expression with `isinstance` or `issubclass`"

    combinable_funcs = ["isinstance", "issubclass"]
    dedupilcation_attr = "value"
    args_to_combine = [1]
    args_to_keep_as_is = [0]

    def make_call_matcher(self, func_name: str) -> m.Call:
        return m.Call(
            func=m.Name(func_name),
            args=[m.Arg(value=m.Name()), m.Arg(value=m.Name() | m.Tuple())],
        )

    def check_calls_same_instance(
        self, left_call: cst.Call, right_call: cst.Call
    ) -> bool:
        return left_call.args[0].value.value == right_call.args[0].value.value
