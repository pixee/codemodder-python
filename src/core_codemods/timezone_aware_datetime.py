import libcst as cst
from libcst import matchers

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
    NewArg,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class TransformDatetimeWithTimezone(LibcstResultTransformer, NameResolutionMixin):

    change_description = "Add `tz=datetime.timezone.utc` to datetime call"
    need_kwarg = (
        "datetime.datetime",
        "datetime.datetime.now",
        "datetime.datetime.fromtimestamp",
    )
    _module_name = "datetime"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if not self.node_is_selected(original_node):
            return updated_node

        match self.find_base_name(original_node):
            case "datetime.datetime.utcnow":
                self.report_change(original_node)
                maybe_name, kwarg_val, module = self._determine_module_and_kwarg(
                    original_node
                )
                new_args = self.replace_args(
                    original_node,
                    [
                        NewArg(
                            name="tz",
                            value=kwarg_val,
                            add_if_missing=True,
                        )
                    ],
                )
                return self.update_call_target(
                    updated_node, module, "now", replacement_args=new_args
                )
            case "datetime.datetime.utcfromtimestamp":
                self.report_change(original_node)
                maybe_name, kwarg_val, module = self._determine_module_and_kwarg(
                    original_node
                )
                if len(original_node.args) != 2 and not self._has_timezone_arg(
                    original_node, "tz"
                ):
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tz",
                                value=kwarg_val,
                                add_if_missing=True,
                            )
                        ],
                    )
                else:
                    new_args = original_node.args

                return self.update_call_target(
                    updated_node,
                    module,
                    "fromtimestamp",
                    replacement_args=new_args,
                )

        return updated_node

    def _determine_module_and_kwarg(self, original_node: cst.Call):

        if maybe_name := self.get_aliased_prefix_name(original_node, self._module_name):
            # it's a regular import OR alias import
            if maybe_name == self._module_name:
                module = "datetime.datetime"
            else:
                module = f"{maybe_name}.datetime"
            kwarg_val = f"{maybe_name}.timezone.utc"
        else:
            # it's from import so timezone should also be from import
            self.add_needed_import("datetime", "timezone")
            kwarg_val = "timezone.utc"
            module = (
                "datetime"
                if (curr_module := original_node.func.value.value)
                in (self._module_name, "date")
                else curr_module
            )

        return maybe_name, kwarg_val, module

    def _has_timezone_arg(self, original_node: cst.Call, name: str) -> bool:
        return any(
            matchers.matches(arg, matchers.Arg(keyword=matchers.Name(name)))
            for arg in original_node.args
        )


TimezoneAwareDatetime = CoreCodemod(
    metadata=Metadata(
        name="timezone-aware-datetime",
        summary="Make `datetime` Calls Timezone-Aware",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(url="https://docs.python.org/3/library/datetime.html"),
        ],
    ),
    transformer=LibcstTransformerPipeline(TransformDatetimeWithTimezone),
)
