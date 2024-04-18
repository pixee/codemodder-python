from pathlib import Path

import libcst as cst
import mock
import pytest
from libcst.codemod import CodemodContext

from codemodder.codemods.api import Metadata, ReviewGuidance, SimpleCodemod
from core_codemods.api import CoreCodemod


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


@pytest.mark.parametrize("ext,call_count", [(".py", 2), (".txt", 1), (".js", 1)])
def test_filter_apply_by_extension(mocker, ext, call_count):
    process_file = mocker.patch("core_codemods.api.CoreCodemod._process_file")

    codemod = CoreCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        default_extensions=[ext],
    )

    codemod.apply(
        mocker.MagicMock(),
        [Path("file.py"), Path("file.txt"), Path("file.js"), Path("file2.py")],
    )

    assert process_file.call_count == call_count
