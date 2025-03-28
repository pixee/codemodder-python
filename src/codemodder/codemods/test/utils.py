import os
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

import mock

from codemodder import registry
from codemodder.codemods.api import BaseCodemod
from codemodder.codetf.v2.codetf import ChangeSet
from codemodder.context import CodemodExecutionContext
from codemodder.diff import create_diff
from codemodder.providers import load_providers


def validate_codemod_registration(codemod_id: str) -> BaseCodemod:
    codemod_registry = registry.load_registered_codemods()
    try:
        return codemod_registry.match_codemods(codemod_include=[codemod_id])[0]
    except IndexError as exc:
        raise IndexError(
            "You must register the codemod to a CodemodCollection."
        ) from exc


class DiffError(Exception):
    """Custom exception to raise when output code != expected output code."""

    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return (
            f"\nExpected:\n\n{self.expected}\n does NOT match actual:\n\n{self.actual}"
        )


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    @property
    def file_extension(self) -> str:
        return "py"

    @classmethod
    def setup_class(cls):
        codemod_id = (
            cls.codemod().id if isinstance(cls.codemod, type) else cls.codemod.id
        )
        cls.codemod = validate_codemod_registration(codemod_id)

    def setup_method(self):
        self.changeset = []

    def run_and_assert(
        self,
        tmpdir,
        input_code,
        expected,
        expected_diff_per_change: list[str] = [],
        num_changes: int = 1,
        min_num_changes: int | None = None,
        root: Path | None = None,
        files: list[Path] | None = None,
        lines_to_exclude: list[int] | None = None,
    ):
        root = root or Path(tmpdir)
        tmp_file_path = files[0] if files else root / f"code.{self.file_extension}"
        tmp_file_path.write_text(dedent(input_code))

        files_to_check = files or [tmp_file_path]

        path_exclude = [f"{tmp_file_path}:{line}" for line in lines_to_exclude or []]

        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=True if expected_diff_per_change else False,
            verbose=False,
            registry=mock.MagicMock(),
            providers=load_providers(),
            repo_manager=mock.MagicMock(),
            path_include=[f"*{f.name}" for f in files_to_check],
            path_exclude=path_exclude,
        )

        self.codemod.apply(
            self.execution_context,
            remediation=True if expected_diff_per_change else False,
        )
        changes = self.execution_context.get_changesets(self.codemod.id)

        self.changeset = changes

        if input_code == expected:
            assert not changes
            return

        self.assert_num_changes(
            changes, num_changes, expected_diff_per_change, min_num_changes
        )

        self.assert_changes(
            tmpdir,
            tmp_file_path,
            input_code,
            expected,
            expected_diff_per_change,
            num_changes,
            changes,
        )

    def assert_num_changes(
        self, changes, expected_num_changes, expected_diff_per_change, min_num_changes
    ):
        if expected_diff_per_change:
            assert len(changes) == expected_num_changes
            actual_num = len(changes)
        else:
            assert len(changes[0].changes) == expected_num_changes
            actual_num = len(changes[0].changes)

        if min_num_changes is not None:
            assert (
                actual_num >= min_num_changes
            ), f"Expected at least {min_num_changes} changes but {actual_num} were created."
        else:
            assert (
                actual_num == expected_num_changes
            ), f"Expected {expected_num_changes} changes but {actual_num} were created."

    def assert_changes(
        self,
        root,
        file_path,
        input_code,
        expected,
        expected_diff_per_change,
        num_changes,
        changes,
    ):
        assert all(
            os.path.relpath(file_path, root) == change.path for change in changes
        )
        assert all(c.description for change in changes for c in change.changes)

        # assert each change individually
        if expected_diff_per_change and num_changes > 1:
            assert num_changes == len(expected_diff_per_change)
            for change, diff in zip(changes, expected_diff_per_change):
                assert change.diff == diff
        else:
            # generate diff from expected code
            expected_diff = create_diff(
                dedent(input_code).splitlines(keepends=True),
                dedent(expected).splitlines(keepends=True),
            )
            try:
                assert expected_diff == changes[0].diff
            except AssertionError:
                raise DiffError(expected_diff, changes[0].diff)

            output_code = file_path.read_bytes().decode("utf-8")

            try:
                assert output_code == (format_expected := dedent(expected))
            except AssertionError:
                raise DiffError(format_expected, output_code)

    def run_and_assert_filepath(
        self,
        root: Path,
        file_path: Path,
        input_code: str,
        expected: str,
        num_changes: int = 1,
        min_num_changes: int | None = None,
    ):
        self.run_and_assert(
            tmpdir=root,
            input_code=input_code,
            expected=expected,
            num_changes=num_changes,
            min_num_changes=min_num_changes,
            files=[file_path],
        )


class BaseDjangoCodemodTest(BaseCodemodTest):
    def create_dir_structure(self, tmpdir):
        django_root = Path(tmpdir) / "mysite"
        settings_folder = django_root / "mysite"
        os.makedirs(settings_folder)
        return (django_root, settings_folder)


class BaseSASTCodemodTest(BaseCodemodTest):
    tool: ClassVar = NotImplemented

    def run_and_assert(
        self,
        tmpdir,
        input_code,
        expected,
        expected_diff_per_change: list[str] | None = None,
        num_changes: int = 1,
        min_num_changes: int | None = None,
        root: Path | None = None,
        files: list[Path] | None = None,
        lines_to_exclude: list[int] | None = None,
        results: str = "",
    ):
        root = root or Path(tmpdir)
        tmp_file_path = files[0] if files else root / f"code.{self.file_extension}"
        tmp_file_path.write_text(dedent(input_code))

        tmp_results_file_path = root / "sast_results"
        tmp_results_file_path.write_text(results)

        files_to_check = files or [tmp_file_path]

        path_exclude = [f"{tmp_file_path}:{line}" for line in lines_to_exclude or []]

        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=True if expected_diff_per_change else False,
            verbose=False,
            tool_result_files_map={self.tool: [tmp_results_file_path]},
            registry=mock.MagicMock(),
            providers=load_providers(),
            repo_manager=mock.MagicMock(),
            path_include=[f"*{f.name}" for f in files_to_check],
            path_exclude=path_exclude,
        )

        self.codemod.apply(
            self.execution_context,
            remediation=True if expected_diff_per_change else False,
        )
        changes = self.execution_context.get_changesets(self.codemod.id)

        if input_code == expected:
            assert not changes
            return

        self.assert_num_changes(
            changes, num_changes, expected_diff_per_change, min_num_changes
        )

        self.assert_findings(changes)

        self.assert_changes(
            tmpdir,
            tmp_file_path,
            input_code,
            expected,
            expected_diff_per_change,
            num_changes,
            changes,
        )

        return changes

    def assert_findings(self, changes: list[ChangeSet]):
        assert all(
            c.fixedFindings for a in changes for c in a.changes
        ), f"Expected all changes to have findings: {changes}"
