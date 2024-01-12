import libcst as cst
from libcst.metadata import GlobalScope, ScopeProvider
from typing import Union
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class RemoveModuleGlobal(BaseCodemod, NameResolutionMixin):
    NAME = "remove-module-global"
    SUMMARY = "Remove `global` Usage at Module Level"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Remove `global` usage at module level."
    REFERENCES: list = []

    def leave_Global(
        self,
        original_node: cst.Global,
        updated_node: cst.Global,
    ) -> Union[cst.Global, cst.RemovalSentinel,]:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node
        scope = self.get_metadata(ScopeProvider, original_node)
        if isinstance(scope, GlobalScope):
            self.report_change(original_node)
            return cst.RemovalSentinel.REMOVE
        return original_node
