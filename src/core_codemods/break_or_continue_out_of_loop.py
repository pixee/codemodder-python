from typing import Union

import libcst as cst
from libcst.codemod import CodemodContext

from codemodder.codemods.base_codemod import Metadata, ReviewGuidance
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import AncestorPatternsMixin
from codemodder.codetf import Reference
from codemodder.file_context import FileContext
from codemodder.result import Result
from core_codemods.api.core_codemod import CoreCodemod


class BreakOrContinueOutOfLoopTransformer(
    LibcstResultTransformer, AncestorPatternsMixin
):

    change_description = "Removed break or continue statement out of loop."

    def __init__(
        self,
        context: CodemodContext,
        results: list[Result] | None,
        file_context: FileContext,
        _transformer: bool = False,
    ):
        self.elses_to_check: set[cst.Else] = set()
        super().__init__(context, results, file_context, _transformer)

    def _handle_break_or_continue(
        self,
        original_node: cst.Break | cst.Continue,
        updated_node: cst.Break | cst.Continue,
    ):
        ancestors = self.path_to_root(original_node)

        # is it inside a for or while ?
        maybe_loop_ancestor = next(
            filter(lambda n: isinstance(n, cst.For | cst.While), ancestors), None
        )
        match maybe_loop_ancestor:
            # ensure it is not insde the else block of a while/for
            case cst.For() | cst.While() as loop:
                if loop.orelse not in ancestors:
                    return updated_node

        self.report_change(original_node)

        # is it directly inside an else body?
        maybe_else_ancestor = next(
            filter(lambda n: isinstance(n, cst.Else), ancestors), None
        )
        match maybe_else_ancestor:
            case cst.Else() as else_node:
                for node in else_node.body.body:
                    if node == original_node:
                        self.elses_to_check.add(else_node)
                    else:
                        match node:
                            case cst.SimpleStatementLine(body=[original_node]):
                                self.elses_to_check.add(else_node)

        return cst.RemovalSentinel.REMOVE

    def leave_Break(self, original_node: cst.Break, updated_node: cst.Break) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
        return self._handle_break_or_continue(original_node, updated_node)

    def leave_Else(self, original_node, updated_node):
        match original_node:
            case cst.Else() if original_node in self.elses_to_check:
                match updated_node.body.body:
                    case []:
                        return cst.RemovalSentinel.REMOVE
        return updated_node

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
