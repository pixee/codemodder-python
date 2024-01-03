import libcst as cst
from libcst.codemod import CodemodContext
import mock

from codemodder.codemods.api import (
    SimpleCodemod,
    Metadata,
    ReviewGuidance,
)


class DoNothingCodemod(SimpleCodemod):
    metadata = Metadata(
        name="do-nothing",
        summary="An identity codemod for testing purposes.",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree


class TestEmptyResults:
    def run_and_assert(self, input_code, expected_output):
        input_tree = cst.parse_module(input_code)
        command_instance = DoNothingCodemod(
            CodemodContext(),
            mock.MagicMock(),
            mock.MagicMock(),
            _transformer=True,
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected_output

    def test_empty_results(self):
        input_code = """print('Hello World')"""
        self.run_and_assert(input_code, input_code)
