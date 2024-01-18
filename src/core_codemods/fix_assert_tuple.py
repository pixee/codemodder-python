import libcst as cst
from typing import List, Union
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod
from codemodder.change import Change
from codemodder.codemods.utils_mixin import NameResolutionMixin


class FixAssertTuple(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="fix-assert-tuple",
        summary="Fix Assert on Populated Tuple",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = (
        "Separate assertion on a populated tuple into multiple assert statements."
    )

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[cst.FlattenSentinel, cst.SimpleStatementLine]:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if len(updated_node.body) == 1 and isinstance(
            assert_node := updated_node.body[0], cst.Assert
        ):
            match assert_test := assert_node.test:
                case cst.Tuple():
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
                    lineNumber=start_line + idx,
                    description=self.change_description,
                )
            )
