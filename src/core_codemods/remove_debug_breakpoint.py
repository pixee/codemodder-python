from typing import Union

import libcst as cst

from codemodder.codemods.utils_mixin import AncestorPatternsMixin, NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class RemoveDebugBreakpoint(SimpleCodemod, NameResolutionMixin, AncestorPatternsMixin):
    metadata = Metadata(
        name="remove-debug-breakpoint",
        summary="Remove Calls to `builtin` `breakpoint` and `pdb.set_trace",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Remove breakpoint call"

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
