from collections import defaultdict
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.process_creation_sandbox import ProcessSandbox
from codemodder.file_context import FileContext


class TestProcessCreationSandbox:
    RESULTS_BY_ID = defaultdict(
        list,
        {
            "sandbox-process-creation": [
                {
                    "fingerprints": {"matchBasedId/v1": "1f266"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/make_process.py",
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "endColumn": 14,
                                    "endLine": 11,
                                    "snippet": {
                                        "text": 'import subprocess\n\nsubprocess.run("echo \'hi\'", shell=True)\nsubprocess.run(["ls", "-l"])\n\nsubprocess.call("echo \'hi\'", shell=True)\nsubprocess.call(["ls", "-l"])\n\nsubprocess.check_output(["ls", "-l"])\n\nvar = "hello"'
                                    },
                                    "startColumn": 1,
                                    "startLine": 1,
                                },
                            }
                        }
                    ],
                    "message": {"text": "Unbounded Process Creation"},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.sandbox-process-creation",
                },
                {
                    "fingerprints": {"matchBasedId/v1": "1f266"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/make_process.py",
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "endColumn": 40,
                                    "endLine": 3,
                                    "snippet": {
                                        "text": "subprocess.run(\"echo 'hi'\", shell=True)"
                                    },
                                    "startColumn": 1,
                                    "startLine": 3,
                                },
                            }
                        }
                    ],
                    "message": {"text": "Unbounded Process Creation"},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.sandbox-process-creation",
                },
                {
                    "fingerprints": {"matchBasedId/v1": "1f266"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/make_process.py",
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "endColumn": 29,
                                    "endLine": 4,
                                    "snippet": {"text": 'subprocess.run(["ls", "-l"])'},
                                    "startColumn": 1,
                                    "startLine": 4,
                                },
                            }
                        }
                    ],
                    "message": {"text": "Unbounded Process Creation"},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.sandbox-process-creation",
                },
                {
                    "fingerprints": {"matchBasedId/v1": "1f266"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/make_process.py",
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "endColumn": 41,
                                    "endLine": 6,
                                    "snippet": {
                                        "text": "subprocess.call(\"echo 'hi'\", shell=True)"
                                    },
                                    "startColumn": 1,
                                    "startLine": 6,
                                },
                            }
                        }
                    ],
                    "message": {"text": "Unbounded Process Creation"},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.sandbox-process-creation",
                },
                {
                    "fingerprints": {"matchBasedId/v1": "1f266"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/make_process.py",
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "endColumn": 30,
                                    "endLine": 7,
                                    "snippet": {
                                        "text": 'subprocess.call(["ls", "-l"])'
                                    },
                                    "startColumn": 1,
                                    "startLine": 7,
                                },
                            }
                        }
                    ],
                    "message": {"text": "Unbounded Process Creation"},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.sandbox-process-creation",
                },
            ]
        },
    )

    def run_and_assert(self, input_code, expected):
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(
            Path("tests/samples/make_process.py"),
            False,
            [],
            [],
            self.RESULTS_BY_ID,
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

    def test_import_subprocess(self):
        input_code = """import subprocess

subprocess.run("echo 'hi'", shell=True)
var = "hello"
"""
        expected = """import subprocess
from security import safe_command

safe_command.run(subprocess.run, "echo 'hi'", shell=True)
var = "hello"
"""
        self.run_and_assert(input_code, expected)

    def test_rule_ids(self):
        assert ProcessSandbox.RULE_IDS == ["sandbox-process-creation"]

    @pytest.mark.skip()
    def test_from_subprocess(self):
        input_code = """from subprocess import run

run("echo 'hi'", shell=True)
var = "hello"
"""
        expected = """from subprocess import run
from security import safe_command

safe_command.run(run, "echo 'hi'", shell=True)
var = "hello"
"""
        self.run_and_assert(input_code, expected)

    def test_subprocess_nameerror(self):
        input_code = """subprocess.run("echo 'hi'", shell=True)

import subprocess
"""
        expected = input_code
        self.run_and_assert(input_code, expected)

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
    def test_other_import_untouched(self, input_code, expected):
        self.run_and_assert(input_code, expected)

    def test_multifunctions(self):
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

        self.run_and_assert(input_code, expected)

    def test_custom_run(self):
        input_code = """from app_funcs import run

run("echo 'hi'", shell=True)"""
        expected = input_code
        self.run_and_assert(input_code, expected)
