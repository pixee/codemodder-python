# pylint: disable=no-member
import json
import os
import pathlib
import subprocess

from codemodder import __VERSION__


class BaseIntegrationTest:
    codemod = NotImplementedError
    code_path = NotImplementedError
    original_code = NotImplementedError
    expected_new_code = NotImplementedError
    output_path = "test-codetf.txt"

    @classmethod
    def teardown_class(cls):
        with open(cls.code_path, "w", encoding="utf-8") as f:
            f.write(cls.original_code)

        pathlib.Path(cls.output_path).unlink(missing_ok=True)

    def _assert_run_fields(self, run, output_path):
        assert run["vendor"] == "pixee"
        assert run["tool"] == "codemodder-python"
        assert run["version"] == __VERSION__
        assert run["elapsed"] != ""
        assert (
            run["commandLine"]
            == f"python -m codemodder tests/samples/ --output {output_path} --codemod-include={self.codemod.NAME}"
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
        assert change["changes"] == []

    def _assert_codetf_output(self):
        with open(self.output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        assert sorted(codetf.keys()) == ["results", "run"]
        run = codetf["run"]
        self._assert_run_fields(run, self.output_path)
        results = codetf["results"]
        self._assert_results_fields(results, self.code_path)

    def test_file_rewritten(self):
        """
        Tests that file is re-written correctly with new code and correct codetf output.

        This test must ensure that original file is returned to previous state.
        Mocks won't work when making a subprocess call so make sure to delete all
        output files
        """

        with open(self.code_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert code == self.original_code

        completed_process = subprocess.run(
            [
                "python",
                "-m",
                "codemodder",
                "tests/samples/",
                "--output",
                self.output_path,
                f"--codemod-include={self.codemod.NAME}",
            ],
            check=False,
        )
        assert completed_process.returncode == 0
        with open(self.code_path, "r", encoding="utf-8") as f:
            new_code = f.read()
        assert new_code == self.expected_new_code

        self._assert_codetf_output()
