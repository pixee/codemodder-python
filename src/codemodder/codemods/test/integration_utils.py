import json
import os
import pathlib
import subprocess
import tempfile
from textwrap import dedent
from types import ModuleType

import jsonschema

from codemodder import __version__, registry

from .validations import execute_code

# SAMPLES_DIR = "tests/samples"
# # Enable import of test modules from test directory
# sys.path.append(SAMPLES_DIR)


class CleanRepoMixin:
    @classmethod
    def teardown_class(cls):
        """Ensure any re-written file is undone after integration test class"""
        # TODO: we should probably use temporary directories instead
        # repo = git.Git(os.getcwd())
        # repo.execute(["git", "checkout", os.path.join(os.getcwd(), SAMPLES_DIR)])
        # pathlib.Path(cls.output_path).unlink(missing_ok=True)
        #
        # os.remove(path)


class DependencyTestMixin:
    # Only for codemods that modify requirements should these be overridden
    requirements_file_name = ""
    original_requirements = ""
    expected_requirements = ""

    def write_original_dependencies(self):
        if self.requirements_file_name:
            with open(self.dependency_path, "w", encoding="utf-8") as f:  # type: ignore
                f.write(self.original_requirements)

    #
    def check_dependencies_after(self):
        if self.requirements_file_name:
            with open(self.dependency_path, "r", encoding="utf-8") as f:
                new_requirements_txt = f.read()
            assert new_requirements_txt == self.expected_requirements

    # todo teardown, delete files


class BaseIntegrationTest(DependencyTestMixin, CleanRepoMixin):
    codemod = NotImplementedError
    original_code = NotImplementedError
    replacement_lines = NotImplementedError
    num_changes = 1
    _lines: list = []
    num_changed_files = 1
    allowed_exceptions = ()
    sonar_issues_json: str | None = None

    @classmethod
    def setup_class(cls):
        cls.codemod_registry = registry.load_registered_codemods()

        # todo: can supply dir to all
        cls.code_path = tempfile.mkstemp(suffix=".py")[1]
        cls.code_dir = os.path.dirname(cls.code_path)
        cls.code_filename = os.path.relpath(cls.code_path, cls.code_dir)
        cls.output_path = tempfile.mkstemp()[1]

        cls.original_code, cls.expected_new_code = original_and_expected_from_code_path(
            cls.original_code, cls.replacement_lines
        )

        if cls.requirements_file_name:
            temp_dir = tempfile.mkdtemp()
            cls.dependency_path = os.path.join(temp_dir, cls.requirements_file_name)

    def setup_method(self):
        # todo move to stup class?
        try:
            name = (
                self.codemod().name
                if isinstance(self.codemod, type)
                else self.codemod.name
            )
            # This is how we ensure that the codemod is actually in the registry
            self.codemod_instance = self.codemod_registry.match_codemods(
                codemod_include=[name]
            )[0]
        except IndexError as exc:
            raise IndexError(
                "You must register the codemod to a CodemodCollection."
            ) from exc

    def _assert_run_fields(self, run, output_path):
        assert run["vendor"] == "pixee"
        assert run["tool"] == "codemodder-python"
        assert run["version"] == __version__
        assert run["elapsed"] != ""
        assert run[
            "commandLine"
        ] == f'codemodder {self.code_dir} --output {output_path} --codemod-include={self.codemod_instance.name} --path-include={self.code_filename} --path-exclude=""' + (
            f" --sonar-issues-json={self.sonar_issues_json}"
            if self.sonar_issues_json
            else ""
        )
        assert run["directory"] == os.path.abspath(self.code_dir)
        assert run["sarifs"] == []

    def _assert_sonar_fields(self, result):
        assert result["detectionTool"]["name"] == "Sonar"
        assert (
            result["detectionTool"]["rule"]["id"]
            == self.codemod_instance._metadata.tool.rule_id
        )
        assert (
            result["detectionTool"]["rule"]["name"]
            == self.codemod_instance._metadata.tool.rule_name
        )
        # TODO: empty array until we add findings metadata
        assert result["detectionTool"]["findings"] == []

    def _assert_results_fields(self, results, output_path):
        assert len(results) == 1
        result = results[0]
        assert result["codemod"] == self.codemod_instance.id
        assert result["references"] == [
            ref.model_dump(exclude_none=True)
            for ref in self.codemod_instance.references
        ]

        assert ("detectionTool" in result) == bool(self.sonar_issues_json)

        # TODO: if/when we add description for each url
        for reference in result["references"][
            # Last reference for Sonar has a different description
            : (-1 if self.sonar_issues_json else None)
        ]:
            assert reference["url"] == reference["description"]

        if self.sonar_issues_json:
            assert self.codemod_instance._metadata.tool is not None
            assert (
                result["references"][-1]["description"]
                == self.codemod_instance._metadata.tool.rule_name
            )
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
        with open(self.code_path, "w", encoding="utf-8") as f:  # type: ignore
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
            f"--codemod-include={self.codemod_instance.name}",
            f"--path-include={self.code_filename}",
            '--path-exclude=""',
        ]

        if self.sonar_issues_json:
            command.append(f"--sonar-issues-json={self.sonar_issues_json}")

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
        # pathlib.Path(self.output_path).unlink(missing_ok=True)
        # self._run_idempotency_check(command)

    def _run_idempotency_check(self, command):
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


def original_and_expected_from_code_path(original_code, replacements):
    """
    Returns a pair (original_code, expected) where original_code contains the contents of the code_path file and expected contains the code_path file where, for each (i,replacement) in replacements, the lines numbered i in original_code are replaced with replacement.
    """
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
