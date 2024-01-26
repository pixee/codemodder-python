# pylint: disable=no-member, protected-access, attribute-defined-outside-init
import git
import json
import os
import pathlib
import subprocess
import sys

from codemodder import __version__
from codemodder import registry
from tests.validations import execute_code

SAMPLES_DIR = "tests/samples"
# Enable import of test modules from test directory
sys.path.append(SAMPLES_DIR)


class CleanRepoMixin:
    @classmethod
    def teardown_class(cls):
        """Ensure any re-written file is undone after integration test class"""
        # TODO: we should probably use temporary directories instead
        repo = git.Git(os.getcwd())
        repo.execute(["git", "checkout", os.path.join(os.getcwd(), SAMPLES_DIR)])

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
    code_path: str = NotImplementedError
    original_code = NotImplementedError
    expected_new_code = NotImplementedError
    output_path = "test-codetf.txt"
    num_changes = 1
    _lines = []
    num_changed_files = 1
    allowed_exceptions = ()

    @classmethod
    def setup_class(cls):
        cls.codemod_registry = registry.load_registered_codemods()

    def setup_method(self):
        try:
            self.codemod_wrapper = self.codemod_registry.match_codemods(
                codemod_include=[self.codemod.name()]
            )[0]
        except IndexError as exc:
            raise IndexError(
                "You must register the codemod to a CodemodCollection."
            ) from exc

    def _assert_run_fields(self, run, output_path):
        code_path = os.path.relpath(self.code_path, SAMPLES_DIR)
        assert run["vendor"] == "pixee"
        assert run["tool"] == "codemodder-python"
        assert run["version"] == __version__
        assert run["elapsed"] != ""
        assert (
            run["commandLine"]
            == f'codemodder {SAMPLES_DIR} --output {output_path} --codemod-include={self.codemod_wrapper.name} --path-include={code_path} --path-exclude=""'
        )
        assert run["directory"] == os.path.abspath(SAMPLES_DIR)
        assert run["sarifs"] == []

    def _assert_results_fields(self, results, output_path):
        assert len(results) == 1
        result = results[0]
        assert result["codemod"] == self.codemod_wrapper.id
        assert result["references"] == self.codemod_wrapper.references

        # TODO: once we add description for each url.
        for reference in result["references"]:
            assert reference["url"] == reference["description"]

        assert len(result["changeset"]) == self.num_changed_files

        # A codemod may change multiple files. For now we will
        # assert the resulting data for one file only.
        change = [
            result for result in result["changeset"] if result["path"] == output_path
        ][0]
        assert change["path"] == output_path
        assert change["diff"] == self.expected_diff

        assert len(change["changes"]) == self.num_changes
        line_change = change["changes"][0]
        assert line_change["lineNumber"] == str(self.expected_line_change)
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
        # CodeTf2 spec requires relative paths
        self._assert_results_fields(
            results, os.path.relpath(self.code_path, SAMPLES_DIR)
        )

    def check_code_before(self):
        with open(self.code_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert code == self.original_code

    def check_code_after(self):
        with open(self.code_path, "r", encoding="utf-8") as f:
            new_code = f.read()
        assert new_code == self.expected_new_code
        execute_code(path=self.code_path, allowed_exceptions=self.allowed_exceptions)

    def test_file_rewritten(self):
        """
        Tests that file is re-written correctly with new code and correct codetf output.

        This test must ensure that original file is returned to previous state.
        Mocks won't work when making a subprocess call so make sure to delete all
        output files
        """
        code_path = os.path.relpath(self.code_path, SAMPLES_DIR)
        command = [
            "codemodder",
            SAMPLES_DIR,
            "--output",
            self.output_path,
            f"--codemod-include={self.codemod_wrapper.name}",
            f"--path-include={code_path}",
            '--path-exclude=""',
        ]

        self.check_code_before()
        self.check_dependencies_before()

        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
        )
        assert completed_process.returncode == 0

        self.check_code_after()
        self.check_dependencies_after()
        self._assert_codetf_output()
        pathlib.Path(self.output_path).unlink(missing_ok=True)
        self._run_idempotency_chec(command)

    def _run_idempotency_chec(self, command):
        # idempotency test, run it again and assert no files changed
        completed_process = subprocess.run(
            command,
            check=False,
        )
        assert completed_process.returncode == 0
        # codemodder stops earlier when no semgrep results are found
        # this output_path file may not exist.
        if pathlib.Path(self.output_path).exists():
            with open(self.output_path, "r", encoding="utf-8") as f:
                codetf = json.load(f)
            assert codetf["results"][0]["changeset"] == []

        with open(self.code_path, "r", encoding="utf-8") as f:
            still_new_code = f.read()
        assert still_new_code == self.expected_new_code


def original_and_expected_from_code_path(code_path, replacements):
    """
    Returns a pair (original_code, expected) where original_code contains the contents of the code_path file and expected contains the code_path file where, for each (i,replacement) in replacements, the lines numbered i in original_code are replaced with replacement.
    """
    lines = _lines_from_codepath(code_path)
    original_code = "".join(lines)
    _replace_lines_with(lines, replacements)
    return (original_code, "".join(lines))


def _lines_from_codepath(code_path):
    with open(code_path, mode="r", encoding="utf-8") as f:
        return f.readlines()


def _replace_lines_with(lines, replacements):
    total_lines = len(lines)
    for lineno, replacement in replacements:
        if lineno >= total_lines:
            lines.extend(replacement)
            continue
        lines[lineno] = replacement
    return lines
