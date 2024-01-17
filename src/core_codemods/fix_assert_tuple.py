import libcst as cst
from typing import List
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class FixAssertTuple(BaseCodemod, NameResolutionMixin):
    NAME = "fix-assert-tuple"
    SUMMARY = "TODISimplify Boolean Expressions Using `startswith` and `endswith`"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "TODOUse tuple of matches instead of boolean expression"
    REFERENCES: list = []

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.FlattenSentinel:  # todo update
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
                    # todo: report change for each added line
                    return cst.FlattenSentinel(new_asserts)
        return updated_node

    def _make_asserts(self, node: cst.Assert) -> List[cst.SimpleStatementLine]:
        return [
            cst.SimpleStatementLine(body=[cst.Assert(test=element.value, msg=node.msg)])
            for element in node.test.elements
        ]
