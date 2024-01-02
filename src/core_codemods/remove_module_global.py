import libcst as cst
from libcst.metadata import GlobalScope, ScopeProvider
from typing import Union
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class RemoveModuleGlobal(BaseCodemod, NameResolutionMixin):
    NAME = "remove-module-global"
    SUMMARY = "Remove Module-level Global Call"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Remove Lines with `global` keyword at Module Level"
    REFERENCES: list = []

    def leave_Global(
        self, original_node: cst.Global, _
    ) -> Union[cst.Global, cst.RemovalSentinel,]:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return original_node
        scope = self.get_metadata(ScopeProvider, original_node)
        if isinstance(scope, GlobalScope):
            self.report_change(original_node)
            return cst.RemovalSentinel.REMOVE
        return original_node
