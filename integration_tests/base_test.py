# pylint: disable=no-member
import git
import json
import os
import pathlib
import subprocess

from codemodder import __VERSION__


class CleanRepoMixin:
    @classmethod
    def teardown_class(cls):
        """Ensure any re-written file is undone after integration test class"""
        repo = git.Git(os.getcwd())
        repo.execute(["git", "checkout", os.getcwd() + "/tests/samples"])

        pathlib.Path(cls.output_path).unlink(missing_ok=True)


class DependencyTestMixin:
    # Only for codemods that modify requirements should these be overridden
    requirements_path = ""
    original_requirements = ""
    expected_new_reqs = ""

    def check_dependencies_before(self):
        if self.requirements_path:
            with open(self.requirements_path, "r", encoding="utf-8") as f:
                requirements_txt = f.read()
            assert requirements_txt == self.original_requirements

    def check_dependencies_after(self):
        if self.requirements_path:
            with open(self.requirements_path, "r", encoding="utf-8") as f:
                new_requirements_txt = f.read()
            assert new_requirements_txt == self.expected_new_reqs


class BaseIntegrationTest(DependencyTestMixin, CleanRepoMixin):
    codemod = NotImplementedError
    code_path = NotImplementedError
    original_code = NotImplementedError
    expected_new_code = NotImplementedError
    output_path = "test-codetf.txt"
    num_changes = 1

    def _assert_run_fields(self, run, output_path):
        assert run["vendor"] == "pixee"
        assert run["tool"] == "codemodder-python"
        assert run["version"] == __VERSION__
        assert run["elapsed"] != ""
        assert (
            run["commandLine"]
            == f"python -m codemodder tests/samples/ --output {output_path} --codemod-include={self.codemod.METADATA.NAME}"
        )
        assert run["directory"] == os.path.abspath("tests/samples/")
        assert run["sarifs"] == []

    def _assert_results_fields(self, results, output_path):
        assert len(results) == 1
        result = results[0]
        assert result["codemod"] == self.codemod.full_name()
        assert len(result["changeset"]) == 1
        change = result["changeset"][0]
        assert change["path"] == output_path
        assert change["diff"] == self.expected_diff

        assert len(change["changes"]) == self.num_changes
        line_change = change["changes"][0]
        assert line_change["lineNumber"] == self.expected_line_change
        assert line_change["description"] == self.change_description
        assert line_change["packageActions"] == []
        assert line_change["properties"] == {}

    def _assert_codetf_output(self):
        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        assert sorted(codetf.keys()) == ["results", "run"]
        run = codetf["run"]
        self._assert_run_fields(run, self.output_path)
        results = codetf["results"]
        self._assert_results_fields(results, self.code_path)

    def check_code_before(self):
        with open(self.code_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert code == self.original_code

    def check_code_after(self):
        with open(self.code_path, "r", encoding="utf-8") as f:
            new_code = f.read()
        assert new_code == self.expected_new_code

    def test_file_rewritten(self):
        """
        Tests that file is re-written correctly with new code and correct codetf output.

        This test must ensure that original file is returned to previous state.
        Mocks won't work when making a subprocess call so make sure to delete all
        output files
        """

        command = [
            "python",
            "-m",
            "codemodder",
            "tests/samples/",
            "--output",
            self.output_path,
            f"--codemod-include={self.codemod.METADATA.NAME}",
        ]

        self.check_code_before()
        self.check_dependencies_before()

        completed_process = subprocess.run(
            command,
            check=False,
        )
        assert completed_process.returncode == 0

        self.check_code_after()
        self.check_dependencies_after()
        self._assert_codetf_output()
        self._run_idempotency_chec(command)

    def _run_idempotency_chec(self, command):
        # idempotency test, run it again and assert no files changed
        completed_process = subprocess.run(
            command,
            check=False,
        )
        assert completed_process.returncode == 0
        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)
        assert codetf["results"] == []
        with open(self.code_path, "r", encoding="utf-8") as f:
            still_new_code = f.read()
        assert still_new_code == self.expected_new_code
