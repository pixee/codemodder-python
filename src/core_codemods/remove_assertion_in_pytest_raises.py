from typing import Union
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

    def leave_With(
        self, original_node: cst.With, updated_node: cst.With
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if not self.filter_by_path_includes_or_excludes(original_node):
            return updated_node

        # Are all items pytest.raises?
        for item in original_node.items:
            match item:
                case cst.WithItem(item=cst.Call() as call):
                    maybe_call_base_name = self.find_base_name(call)
                    if (
                        not maybe_call_base_name
                        or maybe_call_base_name != "pytest.raises"
                    ):
                        return updated_node

                case _:
                    return updated_node

        assert_stmts: list[cst.SimpleStatementLine] = []
        assert_position = len(original_node.body.body)
        new_statement_before_asserts = None
        match original_node.body:
            case cst.SimpleStatementSuite():
                for stmt in reversed(original_node.body.body):
                    match stmt:
                        case cst.Assert():
                            assert_position = assert_position - 1
                            assert_stmts.append(
                                cst.SimpleStatementLine(
                                    body=[
                                        stmt.with_changes(
                                            semicolon=cst.MaybeSentinel.DEFAULT
                                        )
                                    ]
                                )
                            )
                            self.report_change(stmt)
                        case _:
                            break
                new_statement_before_asserts = original_node.body.body[
                    assert_position - 1
                ].with_changes(semicolon=cst.MaybeSentinel.DEFAULT)

            case cst.IndentedBlock():
                for simple_stmt in reversed(original_node.body.body):
                    match simple_stmt:
                        case cst.SimpleStatementLine(body=[*head, cst.Assert() as ast]):
                            assert_position = assert_position - 1
                            self.report_change(ast)
                            if head:
                                # TODO foo(); assert 1; assert 2
                                pass
                            else:
                                assert_stmts.append(simple_stmt)
                        case _:
                            break
                new_statement_before_asserts = original_node.body.body[
                    assert_position - 1
                ]

        if assert_stmts:
            assert_stmts.reverse()
            new_with = updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=[
                        *updated_node.body.body[: assert_position - 1],
                        new_statement_before_asserts,
                    ]
                )
            )
            return cst.FlattenSentinel([new_with, *assert_stmts])

        return updated_node


RemoveAssertionInPytestRaises = CoreCodemod(
    metadata=Metadata(
        name="remove-assertion-in-pytest-raises",
        summary="Moves assertions out of with statement body",
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
