# pylint: disable=no-member,not-callable,attribute-defined-outside-init
import os
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

import mock

from codemodder.context import CodemodExecutionContext
from codemodder.diff import create_diff
from codemodder.registry import CodemodRegistry, CodemodCollection
from codemodder.semgrep import run as semgrep_run


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    def setup_method(self):
        if isinstance(self.codemod, type):
            self.codemod = self.codemod()
        self.changeset = []

    def run_and_assert(  # pylint: disable=too-many-arguments
        self,
        tmpdir,
        input_code,
        expected,
        num_changes: int = 1,
        root: Path | None = None,
        files: list[Path] | None = None,
        lines_to_exclude: list[int] | None = None,
    ):
        root = root or tmpdir
        tmp_file_path = files[0] if files else Path(tmpdir) / "code.py"
        tmp_file_path.write_text(dedent(input_code))

        files_to_check = files or [tmp_file_path]

        path_exclude = [f"{tmp_file_path}:{line}" for line in lines_to_exclude or []]

        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=False,
            verbose=False,
            registry=mock.MagicMock(),
            repo_manager=mock.MagicMock(),
            path_include=[f.name for f in files_to_check],
            path_exclude=path_exclude,
        )

        self.codemod.apply(self.execution_context, files_to_check)
        changes = self.execution_context.get_results(self.codemod.id)

        self.changeset = changes

        if input_code == expected:
            assert not changes
            return

        assert len(changes) == 1
        assert len(changes[0].changes) == num_changes

        self.assert_changes(
            tmpdir,
            tmp_file_path,
            input_code,
            expected,
            changes[0],
        )

    def assert_changes(  # pylint: disable=too-many-arguments
        self, root, file_path, input_code, expected, changes
    ):
        expected_diff = create_diff(
            dedent(input_code).splitlines(keepends=True),
            dedent(expected).splitlines(keepends=True),
        )

        assert expected_diff == changes.diff
        assert os.path.relpath(file_path, root) == changes.path

        with open(file_path, "r", encoding="utf-8") as tmp_file:
            output_code = tmp_file.read()

        assert output_code == dedent(expected)

    def run_and_assert_filepath(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        file_path: Path,
        input_code: str,
        expected: str,
        num_changes: int = 1,
    ):
        self.run_and_assert(
            tmpdir=root,
            input_code=input_code,
            expected=expected,
            num_changes=num_changes,
            files=[file_path],
        )


class BaseSemgrepCodemodTest(BaseCodemodTest):
    @classmethod
    def setup_class(cls):
        collection = CodemodCollection(
            origin="pixee",
            codemods=[cls.codemod],
            docs_module="core_codemods.docs",
            semgrep_config_module="core_codemods.semgrep",
        )
        cls.registry = CodemodRegistry()
        cls.registry.add_codemod_collection(collection)

    def results_by_id_filepath(self, input_code, file_path):
        with open(file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(dedent(input_code))

        name = self.codemod.name
        results = self.registry.match_codemods(codemod_include=[name])
        return semgrep_run(self.execution_context, results[0].yaml_files)


class BaseDjangoCodemodTest(BaseCodemodTest):
    def create_dir_structure(self, tmpdir):
        django_root = Path(tmpdir) / "mysite"
        settings_folder = django_root / "mysite"
        os.makedirs(settings_folder)
        return (django_root, settings_folder)


class BaseSASTCodemodTest(BaseCodemodTest):
    tool: ClassVar = NotImplemented

    def run_and_assert(  # pylint: disable=too-many-arguments
        self,
        tmpdir,
        input_code,
        expected,
        num_changes: int = 1,
        root: Path | None = None,
        files: list[Path] | None = None,
        lines_to_exclude: list[int] | None = None,
        results: str = "",
    ):
        root = root or tmpdir
        tmp_file_path = files[0] if files else Path(tmpdir) / "code.py"
        tmp_file_path.write_text(dedent(input_code))

        tmp_results_file_path = Path(tmpdir) / "sast_results"

        with open(tmp_results_file_path, "w", encoding="utf-8") as results_file:
            results_file.write(results)

        files_to_check = files or [tmp_file_path]

        path_exclude = [f"{tmp_file_path}:{line}" for line in lines_to_exclude or []]

        self.execution_context = CodemodExecutionContext(
            directory=root,
            dry_run=False,
            verbose=False,
            tool_result_files_map={self.tool: [str(tmp_results_file_path)]},
            registry=mock.MagicMock(),
            repo_manager=mock.MagicMock(),
            path_include=[f.name for f in files_to_check],
            path_exclude=path_exclude,
        )

        self.codemod.apply(self.execution_context, files_to_check)
        changes = self.execution_context.get_results(self.codemod.id)

        if input_code == expected:
            assert not changes
            return

        assert len(changes) == 1
        assert len(changes[0].changes) == num_changes

        self.assert_changes(
            tmpdir,
            tmp_file_path,
            input_code,
            expected,
            changes[0],
        )
