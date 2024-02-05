import json
import os
import subprocess
import sys
from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)
from codemodder.dependency import (
    build_dependency_notification,
    build_dependency_is_present_notification,
    Security,
)
from .base_test import DependencyTestMixin, CleanRepoMixin
from security import safe_command


SAMPLES_DIR = "tests/samples"
# Enable import of test modules from test directory
sys.path.append(SAMPLES_DIR)


class TestProgramFails:
    def test_no_project_dir_provided(self):
        completed_process = safe_command.run(subprocess.run, ["codemodder"], check=False)
        assert completed_process.returncode == 3

    def test_codemods_include_exclude_conflict(self):
        completed_process = safe_command.run(subprocess.run, [
                "codemodder",
                "tests/samples/",
                "--output",
                "doesntmatter.txt",
                "--codemod-exclude",
                "secure-random",
                "--codemod-include",
                "secure-random",
            ],
            check=False,
        )
        assert completed_process.returncode == 3

    def test_load_sast_only_by_flag(self, tmp_path):
        tmp_file_path = tmp_path / "sonar.json"
        tmp_file_path.touch()
        completed_process = safe_command.run(subprocess.run, [
                "codemodder",
                "tests/samples/",
                "--sonar-issues-json",
                f"{tmp_file_path}",
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed_process.returncode == 0
        assert RemoveAssertionInPytestRaises.id not in completed_process.stdout


class TestTwoCodemods(DependencyTestMixin, CleanRepoMixin):
    output_path = "test-codetf.txt"
    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\nsecurity~=1.2.0\n"

    def test_two_codemods_add_same_dependency(self):
        """
        Asserts codeTF output in case when two codemods would add the same
        dependency to the project.
        1. The dependency should only be added once to the dependency file.
        2. At this time, the first codemod that runs will have a codetf description for
            the dependency getting added, while the second codemod will state the dependency
            is already present. We may want to change this behavior in the future.
        """
        code_path = os.path.relpath("tests/samples/make_*.py", SAMPLES_DIR)
        first_codemod = "sandbox-process-creation"
        second_codemod = "url-sandbox"
        command = [
            "codemodder",
            SAMPLES_DIR,
            "--output",
            self.output_path,
            f"--codemod-include={first_codemod},{second_codemod}",
            f"--path-include={code_path}",
            '--path-exclude=""',
        ]

        self.check_dependencies_before()
        completed_process = safe_command.run(subprocess.run, command,
            check=False,
            shell=False,
        )
        assert completed_process.returncode == 0

        self.check_dependencies_after()

        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        process_creation_results = codetf["results"][0]
        assert first_codemod in process_creation_results["codemod"]
        assert (
            build_dependency_notification("requirements.txt", Security)
            in process_creation_results["description"]
        )

        url_sandbox_results = codetf["results"][1]
        assert second_codemod in url_sandbox_results["codemod"]
        assert (
            build_dependency_is_present_notification("requirements.txt", Security)
            in url_sandbox_results["description"]
        )
