from typing import Sequence, Union

import libcst as cst

from codemodder.codemods.base_codemod import Metadata, Reference, ReviewGuidance
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api.core_codemod import CoreCodemod


class RemoveAssertionInPytestRaisesTransformer(
    LibcstResultTransformer, NameResolutionMixin
):
    change_description = "Moved assertion out of with statement body"

    def _all_pytest_raises(self, node: cst.With):
        for item in node.items:
            match item:
                case cst.WithItem(item=cst.Call() as call):
                    maybe_call_base_name = self.find_base_name(call)
                    if (
                        not maybe_call_base_name
                        or maybe_call_base_name != "pytest.raises"
                    ):
                        return False

                case _:
                    return False
        return True

    def _build_simple_statement_line(self, node: cst.BaseSmallStatement):
        return cst.SimpleStatementLine(
            body=[node.with_changes(semicolon=cst.MaybeSentinel.DEFAULT)]
        )

    def _remove_last_asserts_from_suite(self, node: Sequence[cst.BaseSmallStatement]):
        assert_position = len(node)
        assert_stmts = []
        new_statement_before_asserts = None
        for stmt in reversed(node):
            match stmt:
                case cst.Assert():
                    assert_position = assert_position - 1
                    assert_stmts.append(self._build_simple_statement_line(stmt))
                case _:
                    break
        if assert_position > 0:
            new_statement_before_asserts = node[assert_position - 1].with_changes(
                semicolon=cst.MaybeSentinel.DEFAULT
            )
        return assert_stmts, assert_position, new_statement_before_asserts

    def _remove_last_asserts_from_IndentedBlock(self, node: cst.IndentedBlock):
        assert_position = len(node.body)
        assert_stmts = []
        new_statement_before_asserts = None
        for simple_stmt in reversed(node.body):
            match simple_stmt:
                case cst.SimpleStatementLine(body=[*head, cst.Assert()] as body):
                    assert_position = assert_position - 1
                    if head:
                        sstmts, s_pos, new_stmt = self._remove_last_asserts_from_suite(
                            body
                        )
                        assert_stmts.extend(sstmts)
                        if new_stmt:
                            new_statement_before_asserts = new_stmt
                            new_statement_before_asserts = simple_stmt.with_changes(
                                body=[
                                    *body[: s_pos - 1],
                                    body[s_pos - 1].with_changes(
                                        semicolon=cst.MaybeSentinel.DEFAULT
                                    ),
                                ]
                            )
                            break
                    else:
                        assert_stmts.append(simple_stmt)
                    if new_statement_before_asserts:
                        break
                case _:
                    if assert_position > 0:
                        new_statement_before_asserts = node.body[assert_position - 1]
                    break
        assert_stmts.reverse()
        return assert_stmts, assert_position, new_statement_before_asserts

    def leave_With(
        self, original_node: cst.With, updated_node: cst.With
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if not self._all_pytest_raises(original_node):
            return updated_node

        assert_stmts: list[cst.SimpleStatementLine] = []
        assert_position = len(original_node.body.body)
        new_statement_before_asserts = None
        match original_node.body:
            case cst.SimpleStatementSuite():
                last_stmt = original_node.body.body[-1]
                if not self.node_is_selected(last_stmt):
                    return updated_node
                (
                    assert_stmts,
                    assert_position,
                    new_statement_before_asserts,
                ) = self._remove_last_asserts_from_suite(original_node.body.body)
                assert_stmts.reverse()
            case cst.IndentedBlock():
                last_stmt = original_node.body.body[-1]
                if not self.node_is_selected(last_stmt):
                    return updated_node
                (
                    assert_stmts,
                    assert_position,
                    new_statement_before_asserts,
                ) = self._remove_last_asserts_from_IndentedBlock(original_node.body)

        if assert_stmts:
            # this means all the statements are asserts
            if new_statement_before_asserts:
                new_with = updated_node.with_changes(
                    body=updated_node.body.with_changes(
                        body=[
                            *updated_node.body.body[: assert_position - 1],
                            new_statement_before_asserts,
                        ]
                    )
                )
            else:
                new_with = updated_node.with_changes(
                    body=updated_node.body.with_changes(
                        body=[cst.SimpleStatementLine(body=[cst.Pass()])]
                    )
                )
            # TODO: need to report change for each line changed
            self.report_change(original_node)
            return cst.FlattenSentinel([new_with, *assert_stmts])

        return updated_node


RemoveAssertionInPytestRaises = CoreCodemod(
    metadata=Metadata(
        name="remove-assertion-in-pytest-raises",
        summary="Moves assertions out of `pytest.raises` scope",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.pytest.org/en/7.4.x/reference/reference.html#pytest-raises",
                description="",
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(RemoveAssertionInPytestRaisesTransformer),
    detector=None,
)
