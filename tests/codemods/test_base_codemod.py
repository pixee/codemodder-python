import libcst as cst
from libcst.codemod import Codemod, CodemodContext
import mock

from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)


class DoNothingCodemod(SemgrepCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION="An identity codemod for testing purposes.",
        NAME="do-nothing",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    SUMMARY = "An identity codemod for testing purposes."
    YAML_FILES = []

    def __init__(self, codemod_context: CodemodContext, *args):
        Codemod.__init__(self, codemod_context)
        SemgrepCodemod.__init__(self, *args)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree


class TestEmptyResults:
    def run_and_assert(self, input_code, expected_output):
        input_tree = cst.parse_module(input_code)
        command_instance = DoNothingCodemod(
            CodemodContext(),
            mock.MagicMock(),
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected_output

    def test_empty_results(self):
        input_code = """print('Hello World')"""
        self.run_and_assert(input_code, input_code)
