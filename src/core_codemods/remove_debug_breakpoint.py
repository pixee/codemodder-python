import libcst as cst
from typing import Union
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin, AncestorPatternsMixin


class RemoveDebugBreakpoint(BaseCodemod, NameResolutionMixin, AncestorPatternsMixin):
    NAME = "remove-debug-breakpoint"
    SUMMARY = "Remove Calls to `builtin` `breakpoint` and `pdb.set_trace"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Remove breakpoint call"
    REFERENCES: list = []

    def leave_Expr(
        self,
        original_node: cst.Expr,
        updated_node: cst.Expr,
    ) -> Union[cst.Expr, cst.RemovalSentinel]:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        match call_node := original_node.value:
            case cst.Call():
                if self.find_base_name(call_node) == "builtins.breakpoint":
                    self.report_change(original_node)
                    return cst.RemovalSentinel.REMOVE
                if self.find_base_name(call_node) == "pdb.set_trace":
                    self.remove_unused_import(call_node)
                    self.report_change(original_node)
                    return cst.RemovalSentinel.REMOVE

        return updated_node
