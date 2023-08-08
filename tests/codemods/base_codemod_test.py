# pylint: disable=no-member,not-callable
import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.file_context import FileContext
from codemodder.semgrep import run_on_directory as semgrep_run
from codemodder.semgrep import find_all_yaml_files
from typing import ClassVar


class BaseCodemodTest:
    codemod: ClassVar = NotImplemented

    def results_by_id(self, input_code, tmpdir):
        tmp_file_path = tmpdir / "code.py"
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        return semgrep_run(
            find_all_yaml_files({self.codemod.METADATA.NAME: self.codemod}), tmpdir
        )

    def run_and_assert(self, tmpdir, input_code, expected):
        input_tree = cst.parse_module(input_code)
        results = self.results_by_id(input_code, tmpdir)[tmpdir / "code.py"]
        file_context = FileContext(
            tmpdir / "code.py",
            False,
            [],
            [],
            results,
        )
        command_instance = self.codemod(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected
