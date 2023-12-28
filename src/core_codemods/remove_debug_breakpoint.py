import libcst as cst
from typing import Union
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin, AncestorPatternsMixin


class RemoveDebugBreakpoint(BaseCodemod, NameResolutionMixin, AncestorPatternsMixin):
    NAME = "remove-debug-breakpoint"
    SUMMARY = "TODORemove Module-level Global Call"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "TODORemove Lines with `global` keyword at Module Level"
    REFERENCES: list = []

    def leave_Expr(
        self, original_node: cst.Expr, _
    ) -> Union[cst.Expr, cst.RemovalSentinel]:
        match call_node := original_node.value:
            case cst.Call():
                if self.find_base_name(
                    call_node
                ) == "breakpoint" and self.is_builtin_function(call_node):
                    self.report_change(original_node)
                    return cst.RemovalSentinel.REMOVE
                if self.find_base_name(call_node) == "pdb.set_trace":
                    self.remove_unused_import(call_node)
                    self.report_change(original_node)
                    return cst.RemovalSentinel.REMOVE

        return original_node
