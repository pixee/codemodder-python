from collections import defaultdict
from typing import DefaultDict
import libcst as cst
from libcst.codemod import Codemod, CodemodContext
import pytest
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

    def __init__(self, context: CodemodContext, *args):
        Codemod.__init__(self, context)
        SemgrepCodemod.__init__(self, *args)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree


class TestEmptyResults:
    RESULTS_BY_ID: DefaultDict = defaultdict()

    def run_and_assert(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        command_instance = DoNothingCodemod(
            CodemodContext(), mock.MagicMock(), self.RESULTS_BY_ID
        )
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output

    def test_empty_results(self):
        input_code = """print('Hello World')"""
        self.run_and_assert(input_code, input_code)


class TestSemgrepCodemod:
    # pylint: disable=unused-variable
    def test_missing_class_attrs(self):
        with pytest.raises(NotImplementedError):

            class MissingInfoCodemod(SemgrepCodemod):
                ...

        with pytest.raises(NotImplementedError):

            class MissingNameCodemod(SemgrepCodemod):
                METADATA = CodemodMetadata(
                    "Description", None, ReviewGuidance.MERGE_WITHOUT_REVIEW
                )

        with pytest.raises(NotImplementedError):

            class MissingDescriptionCodemod(SemgrepCodemod):
                METADATA = CodemodMetadata(
                    "", "Name", ReviewGuidance.MERGE_WITHOUT_REVIEW
                )

        with pytest.raises(NotImplementedError):

            class MissingAuthorCodemod(SemgrepCodemod):
                METADATA = CodemodMetadata(
                    NotImplemented,
                    "Name",
                    ReviewGuidance.MERGE_WITHOUT_REVIEW,
                )
