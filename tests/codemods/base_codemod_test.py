# pylint: disable=no-member,not-callable
import libcst as cst
from libcst.codemod import CodemodContext
from pathlib import Path
import os
from codemodder.file_context import FileContext
from codemodder.semgrep import run_on_directory as semgrep_run
from codemodder.semgrep import find_all_yaml_files
from typing import ClassVar


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    def results_by_id_filepath(self, input_code, root, file_path):
        with open(file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        return semgrep_run(
            find_all_yaml_files({self.codemod.METADATA.NAME: self.codemod}), root
        )

    def run_and_assert_filepath(self, root, file_path, input_code, expected):
        input_tree = cst.parse_module(input_code)
        all_results = self.results_by_id_filepath(input_code, root, file_path)
        results = all_results[str(file_path)]
        file_context = FileContext(
            file_path,
            False,
            [],
            [],
            results,
        )
        command_instance = self.codemod(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def results_by_id(self, input_code, tmpdir):
        tmp_file_path = tmpdir / "code.py"
        return self.results_by_id_filepath(input_code, tmpdir, tmp_file_path)

    def run_and_assert(self, tmpdir, input_code, expected):
        tmp_file_path = tmpdir / "code.py"
        self.run_and_assert_filepath(tmpdir, tmp_file_path, input_code, expected)


class BaseDjangoCodemodTest(BaseCodemodTest):
    def create_dir_structure(self, tmpdir):
        django_root = Path(tmpdir) / "mysite"
        settings_folder = django_root / "mysite"
        os.makedirs(settings_folder)
        return (django_root, settings_folder)
