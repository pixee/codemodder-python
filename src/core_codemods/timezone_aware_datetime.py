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

    change_description = "TODO"
    need_kwarg = (
        "datetime.datetime",
        "datetime.datetime.now",
        "datetime.datetime.fromtimestamp",
    )

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if not self.node_is_selected(original_node):
            return updated_node

        match self.find_base_name(original_node):
            case "datetime.datetime":
                # timezone must be kwarg
                if not self._has_timezone_arg(original_node, "tzinfo"):
                    self.report_change(original_node)
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tzinfo",
                                value="datetime.timezone.utc",
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
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tz",
                                value="datetime.timezone.utc",
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
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tz",
                                value="datetime.timezone.utc",
                                add_if_missing=True,
                            )
                        ],
                    )
                    return self.update_arg_target(updated_node, new_args)
            case name if name in (
                "datetime.datetime.today",
                "datetime.date.today",
                "datetime.datetime.utcnow",
            ):
                self.report_change(original_node)
                new_args = self.replace_args(
                    original_node,
                    [
                        NewArg(
                            name="tz",
                            value="datetime.timezone.utc",
                            add_if_missing=True,
                        )
                    ],
                )
                return self.update_call_target(
                    updated_node, "datetime.datetime", "now", replacement_args=new_args
                )
            case "datetime.date.fromtimestamp":
                self.report_change(original_node)
                if len(original_node.args) != 2 and not self._has_timezone_arg(
                    original_node, "tz"
                ):
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tz",
                                value="datetime.timezone.utc",
                                add_if_missing=True,
                            )
                        ],
                    )
                else:
                    new_args = original_node.args
                # Chains .date() to the end
                res = self.update_call_target(
                    updated_node, "datetime.datetime", replacement_args=new_args
                )
                return cst.parse_expression(self.code(res).strip("\n") + ".date()")
            case "datetime.datetime.utcfromtimestamp":
                self.report_change(original_node)
                if len(original_node.args) != 2 and not self._has_timezone_arg(
                    original_node, "tz"
                ):
                    new_args = self.replace_args(
                        original_node,
                        [
                            NewArg(
                                name="tz",
                                value="datetime.timezone.utc",
                                add_if_missing=True,
                            )
                        ],
                    )
                else:
                    new_args = original_node.args
                return self.update_call_target(
                    updated_node,
                    "datetime.datetime",
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
        summary="TODOAdd timeout to `requests` calls",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="todo##https://docs.python-requests.org/en/master/user/quickstart/#timeouts"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(TransformDatetimeWithTimezone),
)
