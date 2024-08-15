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
            case (
                "datetime.datetime"
                | "datetime.datetime.now"
                | "datetime.datetime.fromtimestamp"
                # | "datetime.datetime.today"
                # | "datetime.datetime.utcnow"
                # | "datetime.datetime.utcfromtimestamp"
                # | "datetime.date.today"
                # | "datetime.date.fromtimestamp"
            ):
                return self.handle_datetime_calls(original_node, updated_node)
        return updated_node

    def handle_datetime_calls(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        match self.find_base_name(original_node):
            case "datetime.datetime":
                if not self._has_timezone_arg(original_node, "tzinfo"):
                    self.report_change(original_node)
                    maybe_name = self.get_aliased_prefix_name(
                        original_node, self._module_name
                    )
                    if not maybe_name:
                        # it's from import so timezone should also be from import
                        self.add_needed_import("datetime", "timezone")
                        kwarg_val = "timezone.utc"
                    else:
                        kwarg_val = f"{maybe_name}.timezone.utc"
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tzinfo",
                                value=kwarg_val,
                                add_if_missing=True,
                            )
                        ],
                    )
                    return self.update_arg_target(updated_node, new_args)
            case "datetime.datetime.now":
                # timezone can be pos arg or kwarg
                if not original_node.args and not self._has_timezone_arg(
                    original_node, "tz"
                ):
                    self.report_change(original_node)
                    maybe_name = self.get_aliased_prefix_name(
                        original_node, self._module_name
                    )
                    if not maybe_name:
                        # it's from import so timezone should also be from import
                        self.add_needed_import("datetime", "timezone")
                        kwarg_val = "timezone.utc"
                    else:
                        kwarg_val = f"{maybe_name}.timezone.utc"

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
                    return self.update_arg_target(updated_node, new_args)
            case "datetime.datetime.fromtimestamp":
                # timezone can be pos arg or kwarg
                if len(original_node.args) != 2 and not self._has_timezone_arg(
                    original_node, "tz"
                ):
                    self.report_change(original_node)
                    maybe_name = self.get_aliased_prefix_name(
                        original_node, self._module_name
                    )
                    if not maybe_name:
                        # it's from import so timezone should also be from import
                        self.add_needed_import("datetime", "timezone")
                        kwarg_val = "timezone.utc"
                    else:
                        kwarg_val = f"{maybe_name}.timezone.utc"

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
                    return self.update_arg_target(updated_node, new_args)
            case name if name in (
                "datetime.datetime.today",
                "datetime.datetime.utcnow",
            ):
                self.report_change(original_node)
                maybe_name = self.get_aliased_prefix_name(
                    original_node, self._module_name
                )
                if maybe_name:
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
                        == self._module_name
                        else curr_module
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
            case "datetime.date.today":
                self.report_change(original_node)
                maybe_name = self.get_aliased_prefix_name(
                    original_node, self._module_name
                )
                if maybe_name:
                    # it's a regular import OR alias import
                    if maybe_name == self._module_name:
                        module = "datetime.datetime"
                    else:
                        module = f"{maybe_name}.datetime"
                    kwarg_val = f"{maybe_name}.timezone.utc"
                else:
                    # it's from import so timezone should also be from import
                    self.add_needed_import("datetime", "timezone")
                    # remove `date` import if unused
                    self.remove_unused_import(original_node)
                    kwarg_val = "timezone.utc"
                    module = (
                        "datetime"
                        if (curr_module := original_node.func.value.value)
                        in (self._module_name, "date")
                        else curr_module
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
                # Chains .date() to the end
                res = self.update_call_target(
                    updated_node, module, "now", replacement_args=new_args
                )
                return cst.parse_expression(self.code(res).strip("\n") + ".date()")

            case "datetime.date.fromtimestamp":
                self.report_change(original_node)
                maybe_name = self.get_aliased_prefix_name(
                    original_node, self._module_name
                )

                if maybe_name:
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
                # Chains .date() to the end
                res = self.update_call_target(
                    updated_node, module, replacement_args=new_args
                )
                return cst.parse_expression(self.code(res).strip("\n") + ".date()")
            case "datetime.datetime.utcfromtimestamp":
                self.report_change(original_node)
                maybe_name = self.get_aliased_prefix_name(
                    original_node, self._module_name
                )
                if maybe_name:
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

    def _has_timezone_arg(self, original_node: cst.Call, name: str) -> bool:
        return any(
            matchers.matches(arg, matchers.Arg(keyword=matchers.Name(name)))
            for arg in original_node.args
        )


TimezoneAwareDatetime = CoreCodemod(
    metadata=Metadata(
        name="timezone-aware-datetime",
        summary="Add `tz=datetime.timezone.utc` to datetime Call",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(url="https://docs.python.org/3/library/datetime.html"),
        ],
    ),
    transformer=LibcstTransformerPipeline(TransformDatetimeWithTimezone),
)
