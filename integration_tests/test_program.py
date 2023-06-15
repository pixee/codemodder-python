import json
import os
import pathlib
import subprocess
from codemodder import __VERSION__


class TestProgramFails:
    def test_no_project_dir_provided(self):
        completed_process = subprocess.run(["python", "-m", "codemodder"], check=False)
        assert completed_process.returncode == 1

    def test_codemods_include_exclude_conflict(self):
        completed_process = subprocess.run(
            [
                "python",
                "-m",
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
        # Change this test because it could error `1` for any other reason, too
        # so it's not a good test
        assert completed_process.returncode == 1


class TestOutputs:
    def _assert_run_fields(self, run, output_path):
        assert run["vendor"] == "pixee"
        assert run["tool"] == "codemodder-python"
        assert run["version"] == __VERSION__
        assert run["elapsed"] != ""
        assert (
            run["commandLine"]
            == f"python -m codemodder tests/samples/ --output {output_path} --codemod-include=url-sandbox"
        )
        assert run["directory"] == os.path.abspath("tests/samples/")
        assert run["sarifs"] == []

    def _assert_results_fields(self, results, output_path):
        assert len(results) == 1
        result = results[0]
        assert result["codemod"] == "pixee:python/url-sandbox"
        assert len(result["changeset"]) == 1
        change = result["changeset"][0]
        assert change["path"] == output_path
        assert change["changes"] == []

    def _assert_codetf_output(self, output_path, code_path):
        with open(output_path, "r", encoding="utf-8") as f:
            codetf = json.load(f)

        assert sorted(codetf.keys()) == ["results", "run"]
        run = codetf["run"]
        self._assert_run_fields(run, output_path)
        results = codetf["results"]
        self._assert_results_fields(results, code_path)

    # TODO this test will rewrite the original sample file when failing, change it
    def test_file_rewritten(self):
        """
        Tests that file is re-written correctly with new code and correct codetf output.

        This test must ensure that original file is returned to previous state.
        Mocks won't work when making a subprocess call so make sure to delete all
        output files
        """
        code_path = "tests/samples/make_request.py"
        expected_original_code = (
            'import requests\n\nrequests.get("www.google.com")\nvar = "hello"\n'
        )
        expected_new_code = 'import pixee.safe_requests as safe_requests\n\nsafe_requests.get("www.google.com")\nvar = "hello"\n'
        with open(code_path, "r", encoding="utf-8") as f:
            original_code = f.read()
        assert original_code == expected_original_code

        output_path = "test-codetf.txt"
        completed_process = subprocess.run(
            [
                "python",
                "-m",
                "codemodder",
                "tests/samples/",
                "--output",
                output_path,
                "--codemod-include=url-sandbox",
            ],
            check=False,
        )
        assert completed_process.returncode == 0
        with open("tests/samples/make_request.py", "r", encoding="utf-8") as f:
            new_code = f.read()
        assert new_code == expected_new_code
        with open("tests/samples/make_request.py", "w", encoding="utf-8") as f:
            f.write(original_code)

        self._assert_codetf_output(output_path, code_path)
        pathlib.Path(output_path).unlink(missing_ok=True)
