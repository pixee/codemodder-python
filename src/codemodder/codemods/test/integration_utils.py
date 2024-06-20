import json
import os
import pathlib
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from types import ModuleType

import jsonschema

from codemodder import __version__
from core_codemods.sonar.api import process_sonar_findings

from .utils import validate_codemod_registration
from .validations import execute_code


class DependencyTestMixin:
    # Only for codemods that modify requirements should these be overridden
    requirements_file_name = ""
    original_requirements = ""
    expected_requirements = ""

    def write_original_dependencies(self):
        if self.requirements_file_name:
            with open(self.dependency_path, "w", encoding="utf-8") as f:
                f.write(self.original_requirements)

    def check_dependencies_after(self):
        if self.requirements_file_name:
            with open(self.dependency_path, "r", encoding="utf-8") as f:
                new_requirements_txt = f.read()
            assert new_requirements_txt == self.expected_requirements


class BaseIntegrationTest(DependencyTestMixin):
    codemod = NotImplementedError
    original_code = NotImplementedError
    replacement_lines = NotImplementedError
    num_changes = 1
    _lines: list = []
    num_changed_files = 1
    allowed_exceptions = ()
    sonar_issues_json: str | None = None
    sonar_hotspots_json: str | None = None

    @classmethod
    def setup_class(cls):
        codemod_id = (
            cls.codemod().id if isinstance(cls.codemod, type) else cls.codemod.id
        )
        cls.codemod_instance = validate_codemod_registration(codemod_id)

        cls.output_path = tempfile.mkstemp()[1]
        cls.code_dir = tempfile.mkdtemp()

        if not hasattr(cls, "code_filename"):
            # Only a few codemods require the analyzed file to have a specific filename
            # All others can just be `code.py`
            cls.code_filename = "code.py"

        cls.code_path = os.path.join(cls.code_dir, cls.code_filename)

        if cls.code_filename == "settings.py" and "Django" in str(cls):
            # manage.py must be in the directory above settings.py for this codemod to run
            parent_dir = Path(cls.code_dir).parent
            manage_py_path = parent_dir / "manage.py"
            manage_py_path.touch()

        if hasattr(cls, "expected_new_code"):
            # Some tests are easier to understand with the expected new code provided
            # instead of calculated
            cls.original_code = dedent(cls.original_code).strip("\n")
            cls.expected_new_code = dedent(cls.expected_new_code).strip("\n")
        else:
            cls.original_code, cls.expected_new_code = original_and_expected(
                cls.original_code, cls.replacement_lines
            )

        if cls.requirements_file_name:
            cls.dependency_path = os.path.join(cls.code_dir, cls.requirements_file_name)

    @classmethod
    def teardown_class(cls):
        """Ensure any re-written file is undone after integration test class"""
        pathlib.Path(cls.output_path).unlink(missing_ok=True)
        pathlib.Path(cls.code_path).unlink(missing_ok=True)

        if cls.requirements_file_name:
            pathlib.Path(cls.dependency_path).unlink(missing_ok=True)

    def _assert_run_fields(self, run, output_path):
        assert run["vendor"] == "pixee"
        assert run["tool"] == "codemodder-python"
        assert run["version"] == __version__
        assert run["elapsed"] != ""
        assert run[
            "commandLine"
        ] == f'codemodder {self.code_dir} --output {output_path} --codemod-include={self.codemod_instance.id} --path-include={self.code_filename} --path-exclude=""' + (
            f" --sonar-issues-json={self.sonar_issues_json}"
            if self.sonar_issues_json
            else ""
        ) + (
            f" --sonar-hotspots-json={self.sonar_hotspots_json}"
            if self.sonar_hotspots_json
            else ""
        )
        assert run["directory"] == os.path.abspath(self.code_dir)
        assert run["sarifs"] == []

    def _assert_results_fields(self, results, output_path):
        assert len(results) == 1
        result = results[0]
        assert result["codemod"] == self.codemod_instance.id
        assert result["references"] == [
            ref.model_dump(exclude_none=True)
            for ref in self.codemod_instance.references
        ]

        assert ("detectionTool" in result) == bool(self.sonar_issues_json)
        assert ("detectionTool" in result) == bool(self.sonar_hotspots_json)

        # TODO: if/when we add description for each url
        for reference in result["references"][
            # Last reference for Sonar has a different description
            : (-1 if self.sonar_issues_json or self.sonar_hotspots_json else None)
        ]:
            assert reference["url"] == reference["description"]

        self._assert_sonar_fields(result)

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
        assert line_change["lineNumber"] == int(self.expected_line_change)
        assert line_change["description"] == self.change_description

    def _assert_sonar_fields(self, result):
        del result

    def _assert_codetf_output(self, codetf_schema):
        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        jsonschema.validate(codetf, codetf_schema)

        assert sorted(codetf.keys()) == ["results", "run"]
        run = codetf["run"]
        self._assert_run_fields(run, self.output_path)
        results = codetf["results"]
        # CodeTf2 spec requires relative paths
        self._assert_results_fields(results, self.code_filename)

    def write_original_code(self):
        with open(self.code_path, "w", encoding="utf-8") as f:
            f.write(self.original_code)

    def check_code_after(self) -> ModuleType:
        with open(self.code_path, "r", encoding="utf-8") as f:  # type: ignore
            new_code = f.read()
        assert new_code == self.expected_new_code  # type: ignore
        return execute_code(
            path=self.code_path, allowed_exceptions=self.allowed_exceptions  # type: ignore
        )

    def test_file_rewritten(self, codetf_schema):
        """
        Tests that file is re-written correctly with new code and correct codetf output.

        This test must ensure that original file is returned to previous state.
        Mocks won't work when making a subprocess call so make sure to delete all
        output files
        """
        command = [
            "codemodder",
            self.code_dir,
            "--output",
            self.output_path,
            f"--codemod-include={self.codemod_instance.id}",
            f"--path-include={self.code_filename}",
            '--path-exclude=""',
        ]

        if self.sonar_issues_json:
            command.append(f"--sonar-issues-json={self.sonar_issues_json}")
        if self.sonar_hotspots_json:
            command.append(f"--sonar-hotspots-json={self.sonar_hotspots_json}")

        self.write_original_code()
        self.write_original_dependencies()

        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
        )
        assert completed_process.returncode == 0

        self.check_code_after()
        self.check_dependencies_after()
        self._assert_codetf_output(codetf_schema)
        self._run_idempotency_check(command)

    def _run_idempotency_check(self, command):
        # idempotency test, run it again and assert no files changed
        completed_process = subprocess.run(
            command,
            check=False,
        )
        assert completed_process.returncode == 0

        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)
        assert codetf["results"][0]["changeset"] == []

        with open(self.code_path, "r", encoding="utf-8") as f:
            still_new_code = f.read()
        assert still_new_code == self.expected_new_code


SAMPLES_DIR = "tests/samples"
# Enable import of test modules from test directory
sys.path.append(SAMPLES_DIR)


class SonarIntegrationTest(BaseIntegrationTest):
    """
    Sonar integration tests must use code from a file in tests/samples
    because those files are what appears in sonar_issues.json
    """

    code_path = NotImplementedError
    sonar_issues_json = "tests/samples/sonar_issues.json"
    sonar_hotspots_json = "tests/samples/sonar_hotspots.json"

    @classmethod
    def setup_class(cls):
        codemod_id = (
            cls.codemod().id if isinstance(cls.codemod, type) else cls.codemod.id
        )
        cls.codemod_instance = validate_codemod_registration(codemod_id)

        cls.output_path = tempfile.mkstemp()[1]
        cls.code_dir = SAMPLES_DIR
        cls.code_filename = os.path.relpath(cls.code_path, SAMPLES_DIR)

        if hasattr(cls, "expected_new_code"):
            # Some tests are easier to understand with the expected new code provided
            # instead of calculated
            cls.original_code = "".join(_lines_from_codepath(cls.code_path))
            cls.expected_new_code = dedent(cls.expected_new_code)
        else:
            cls.original_code, cls.expected_new_code = (
                original_and_expected_from_code_path(
                    cls.code_path, cls.replacement_lines
                )
            )

        # TODO: support sonar integration tests that add a dependency to
        # `requirements_file_name`. These tests would not be able to run
        # in parallel at this time since they would all override the same
        # tests/samples/requirements.txt file, unless we change that to
        # a temporary file.
        cls.check_sonar_issues()

    @classmethod
    def teardown_class(cls):
        """Ensure any re-written file is undone after integration test class"""
        pathlib.Path(cls.output_path).unlink(missing_ok=True)
        # Revert code file
        with open(cls.code_path, mode="w", encoding="utf-8") as f:
            f.write(cls.original_code)

    @classmethod
    def check_sonar_issues(cls):
        sonar_results = process_sonar_findings(
            (cls.sonar_issues_json, cls.sonar_hotspots_json)
        )

        assert (
            cls.codemod.requested_rules[-1] in sonar_results
        ), f"Make sure to add a sonar issue/hotspot for {cls.codemod.rule_id} in {cls.sonar_issues_json} or {cls.sonar_hotspots_json}"
        results_for_codemod = sonar_results[cls.codemod.requested_rules[-1]]
        file_path = pathlib.Path(cls.code_filename)
        assert (
            file_path in results_for_codemod
        ), f"Make sure to add a sonar issue/hotspot for file `{cls.code_filename}` under rule `{cls.codemod.rule_id}`in {cls.sonar_issues_json} or {cls.sonar_hotspots_json}"

    def _assert_sonar_fields(self, result):
        assert self.codemod_instance._metadata.tool is not None
        assert (
            result["references"][-1]["description"]
            == self.codemod_instance._metadata.tool.rules[0].name
        )
        assert result["detectionTool"]["name"] == "Sonar"


def original_and_expected_from_code_path(code_path, replacements):
    """
    Returns a pair (original_code, expected) where original_code contains the contents of the code_path file and expected contains the code_path file where, for each (i,replacement) in replacements, the lines numbered i in original_code are replaced with replacement.
    """
    lines = _lines_from_codepath(code_path)
    original_raw_code = "".join(lines)
    _replace_lines_with(lines, replacements)
    return (original_raw_code, "".join(lines))


def _lines_from_codepath(code_path):
    with open(code_path, mode="r", encoding="utf-8") as f:
        return f.readlines()


def original_and_expected(original_code, replacements):
    original_code = dedent(original_code).strip("\n")
    lines = original_code.split("\n")
    lines = [line + "\n" for line in lines]
    _replace_lines_with(lines, replacements)
    return (original_code + "\n", "".join(lines))


def _replace_lines_with(lines, replacements):
    total_lines = len(lines)
    for lineno, replacement in replacements:
        if lineno >= total_lines + 1:
            lines.extend(replacement)
            continue
        lines[lineno - 1] = replacement
    return lines
