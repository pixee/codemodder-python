from pathlib import Path

import libcst as cst
import mock
import pytest
from libcst.codemod import CodemodContext

from codemodder.codemods.api import Metadata, ReviewGuidance, SimpleCodemod
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from core_codemods.api import CoreCodemod, SASTCodemod


class DoNothingCodemod(SimpleCodemod):
    metadata = Metadata(
        name="do-nothing",
        summary="An identity codemod for testing purposes.",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree


class FakeSASTCodemod(SASTCodemod):
    @property
    def origin(self):
        return "fake"


class MockContext(CodemodExecutionContext):
    def __init__(self, directory=None, files_to_analyze=None, path_include=None):
        super().__init__(
            directory=directory or Path("."),
            dry_run=False,
            verbose=False,
            registry=mock.MagicMock(default_include_paths=["*.py"]),
            providers=mock.MagicMock(),
            repo_manager=mock.MagicMock(),
            path_include=path_include or [],
            path_exclude=[],
            tool_result_files_map={},
        )

        self.files_to_analyze = files_to_analyze or []


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
def test_core_codemod_filter_apply_by_extension(mocker, ext, call_count):
    process_file = mocker.patch("core_codemods.api.CoreCodemod._process_file")

    codemod = CoreCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        default_extensions=[ext],
    )

    context = mocker.MagicMock()
    context.find_and_fix_paths = [
        Path("file.py"),
        Path("file.txt"),
        Path("file.js"),
        Path("file2.py"),
    ]

    codemod.apply(context)

    assert process_file.call_count == call_count


def test_core_codemod_filter_default_path_exclude(mocker):
    codemod = CoreCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        default_extensions=[".py"],
    )

    context = MockContext(
        files_to_analyze=[
            Path("file.py"),
            Path("tests/file2.py"),
            Path(".tox/file3.py"),
        ]
    )

    assert codemod.get_files_to_analyze(context, None) == [Path("file.py")]


def test_core_codemod_filter_with_path_include(mocker):
    codemod = CoreCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        default_extensions=[".py"],
    )

    context = MockContext(
        files_to_analyze=[
            Path("file.py"),
            Path("bar.py"),
            Path("tests/file2.py"),
            Path(".tox/file3.py"),
        ],
        path_include=["*file.py"],
    )

    assert codemod.get_files_to_analyze(context, None) == [Path("file.py")]


def test_sast_codemod_filter_no_findings(mocker):
    codemod = FakeSASTCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        requested_rules=["fake-rule"],
        default_extensions=[".py"],
    )

    context = MockContext(
        directory=Path("."),
        files_to_analyze=[Path("file.py"), Path("foo.py"), Path("bar.py")],
    )

    assert codemod.get_files_to_analyze(context, ResultSet()) == []


def test_sast_codemod_filter_with_findings(mocker):
    codemod = FakeSASTCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        requested_rules=["fake-rule"],
        default_extensions=[".py"],
    )

    context = MockContext(
        directory=Path("."),
        files_to_analyze=[Path("file.py"), Path("foo.py"), Path("bar.py")],
    )

    results = ResultSet(
        {
            "fake-rule": {
                Path("file.py"): [mocker.MagicMock()],
                Path("foo.py"): [mocker.MagicMock()],
            }
        }
    )

    assert codemod.get_files_to_analyze(context, results) == [
        Path("file.py"),
        Path("foo.py"),
    ]


def test_sast_codemod_filter_by_findings_with_extension(mocker):
    codemod = FakeSASTCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        requested_rules=["fake-rule"],
        default_extensions=[".py"],
    )

    context = MockContext(
        directory=Path("."),
        files_to_analyze=[Path("file.py"), Path("foo.txt"), Path("bar.py")],
    )

    results = ResultSet(
        {
            "fake-rule": {
                Path("file.py"): [mocker.MagicMock()],
                Path("foo.txt"): [mocker.MagicMock()],
            }
        }
    )

    assert codemod.get_files_to_analyze(context, results) == [Path("file.py")]


def test_sast_codemod_filter_by_findings_with_path_include(mocker):
    codemod = FakeSASTCodemod(
        metadata=mocker.MagicMock(),
        transformer=mocker.MagicMock(),
        requested_rules=["fake-rule"],
        default_extensions=[".py"],
    )

    context = MockContext(
        directory=Path("."),
        files_to_analyze=[Path("file.py"), Path("foo.py"), Path("bar.py")],
        path_include=["*file.py"],
    )

    results = ResultSet(
        {
            "fake-rule": {
                Path("file.py"): [mocker.MagicMock()],
                Path("foo.py"): [mocker.MagicMock()],
            }
        }
    )

    assert codemod.get_files_to_analyze(context, results) == [Path("file.py")]
