from typing import Union

import libcst as cst
from libcst.metadata import GlobalScope, ScopeProvider

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class RemoveModuleGlobal(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="remove-module-global",
        summary="Remove `global` Usage at Module Level",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Remove `global` usage at module level."

    def leave_Global(
        self,
        original_node: cst.Global,
        updated_node: cst.Global,
    ) -> Union[
        cst.Global,
        cst.RemovalSentinel,
    ]:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node
        scope = self.get_metadata(ScopeProvider, original_node)
        if isinstance(scope, GlobalScope):
            self.report_change(original_node)
            return cst.RemovalSentinel.REMOVE
        return original_node
