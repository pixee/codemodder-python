from collections import defaultdict
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.process_creation_sandbox import ProcessSandbox
from codemodder.file_context import FileContext
from codemodder.semgrep import find_all_yaml_files, run_on_directory as semgrep_run


class TestProcessCreationSandbox:
    def results_by_id(self, input_code, tmpdir):
        tmp_file_path = tmpdir / "code.py"
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        return semgrep_run(
            find_all_yaml_files({ProcessSandbox.METADATA.NAME: ProcessSandbox}), tmpdir
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
        command_instance = ProcessSandbox(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def test_with_empty_results(self):
        input_code = """import subprocess

subprocess.run("echo 'hi'", shell=True)
var = "hello"
"""
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(
            Path("tests/samples/make_process.py"),
            False,
            [],
            [],
            defaultdict(list),
        )
        command_instance = ProcessSandbox(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == input_code

    def test_import_subprocess(self, tmpdir):
        input_code = """import subprocess

subprocess.run("echo 'hi'", shell=True)
var = "hello"
"""
        expected = """import subprocess
from security import safe_command

safe_command.run(subprocess.run, "echo 'hi'", shell=True)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_rule_ids(self):
        assert ProcessSandbox.RULE_IDS == ["sandbox-process-creation"]

    @pytest.mark.skip()
    def test_from_subprocess(self, tmpdir):
        input_code = """from subprocess import run

run("echo 'hi'", shell=True)
var = "hello"
"""
        expected = """from subprocess import run
from security import safe_command

safe_command.run(run, "echo 'hi'", shell=True)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_subprocess_nameerror(self, tmpdir):
        input_code = """subprocess.run("echo 'hi'", shell=True)

import subprocess
"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "input_code,expected",
        [
            (
                """import subprocess
import csv
subprocess.run("echo 'hi'", shell=True)
csv.excel
""",
                """import subprocess
import csv
from security import safe_command

safe_command.run(subprocess.run, "echo 'hi'", shell=True)
csv.excel
""",
            ),
            (
                """import subprocess
from csv import excel
subprocess.run("echo 'hi'", shell=True)
excel
""",
                """import subprocess
from csv import excel
from security import safe_command

safe_command.run(subprocess.run, "echo 'hi'", shell=True)
excel
""",
            ),
        ],
    )
    def test_other_import_untouched(self, tmpdir, input_code, expected):
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multifunctions(self, tmpdir):
        # Test that subprocess methods that aren't part of the codemod are not changed.
        # If we add the function as one of
        # our codemods, this test would change.
        input_code = """import subprocess

subprocess.run("echo 'hi'", shell=True)
subprocess.check_output(["ls", "-l"])
        """

        expected = """import subprocess
from security import safe_command

safe_command.run(subprocess.run, "echo 'hi'", shell=True)
subprocess.check_output(["ls", "-l"])"""

        self.run_and_assert(tmpdir, input_code, expected)

    def test_custom_run(self, tmpdir):
        input_code = """from app_funcs import run

run("echo 'hi'", shell=True)"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)
