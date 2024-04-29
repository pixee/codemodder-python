from typing import Union

import libcst as cst

from codemodder.codemods.base_codemod import Metadata, ReviewGuidance
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import AncestorPatternsMixin
from codemodder.codetf import Reference
from core_codemods.api.core_codemod import CoreCodemod


class BreakOrContinueOutOfLoopTransformer(
    LibcstResultTransformer, AncestorPatternsMixin
):

    change_description = "Removed break or continue statement out of loop."

    def _handle_break_or_continue(
        self,
        original_node: cst.Break | cst.Continue,
        updated_node: cst.Break | cst.Continue,
    ):
        ancestors = self.path_to_root(original_node)
        # is it inside a for or while ?
        if any(filter(lambda n: isinstance(n, cst.For | cst.While), ancestors)):
            return updated_node
        self.report_change(original_node)
        return cst.RemovalSentinel.REMOVE

    def leave_Break(self, original_node: cst.Break, updated_node: cst.Break) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
        return self._handle_break_or_continue(original_node, updated_node)

    def leave_Continue(
        self, original_node: cst.Continue, updated_node: cst.Continue
    ) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
        return self._handle_break_or_continue(original_node, updated_node)


BreakOrContinueOutOfLoop = CoreCodemod(
    metadata=Metadata(
        name="break-or-continue-out-of-loop",
        summary="Removed break or continue statement out of loop",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://pylint.readthedocs.io/en/stable/user_guide/messages/error/not-in-loop.html"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(BreakOrContinueOutOfLoopTransformer),
    detector=None,
)
