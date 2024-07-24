from typing import List, Union

import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.codetf import Change
from core_codemods.api import Metadata, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class FixAssertTupleTransform(LibcstResultTransformer, NameResolutionMixin):
    change_description = "Separate assertion on a non-empty tuple literal into multiple assert statements."

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[cst.FlattenSentinel, cst.SimpleStatementLine]:

        if len(original_node.body) == 1 and isinstance(
            assert_node := original_node.body[0], cst.Assert
        ):
            match assert_test := assert_node.test:
                case cst.Tuple():
                    if not self.node_is_selected(assert_test):
                        return updated_node

                    if not assert_test.elements:
                        return updated_node
                    new_asserts = self._make_asserts(assert_node)
                    self._report_new_lines(original_node, len(new_asserts))
                    return cst.FlattenSentinel(new_asserts)
        return updated_node

    def _make_asserts(self, node: cst.Assert) -> List[cst.SimpleStatementLine]:
        return [
            cst.SimpleStatementLine(body=[cst.Assert(test=element.value, msg=node.msg)])
            for element in node.test.elements
        ]

    def _report_new_lines(
        self, original_node: cst.SimpleStatementLine, newlines_count: int
    ):
        start_line = self.node_position(original_node).start.line
        for idx in range(newlines_count):
            self.file_context.codemod_changes.append(
                Change(
                    lineNumber=(line_number := start_line + idx),
                    description=self.change_description,
                    # For now we can only link the finding to the first line changed
                    findings=self.file_context.get_findings_for_location(line_number),
                )
            )


FixAssertTuple = CoreCodemod(
    metadata=Metadata(
        name="fix-assert-tuple",
        summary="Fix `assert` on Non-Empty Tuple Literal",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[],
    ),
    transformer=LibcstTransformerPipeline(FixAssertTupleTransform),
    detector=None,
)
