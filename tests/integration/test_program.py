import pathlib
import subprocess


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


class TestFileRewrite:
    def test_file_rewritten(self):
        """
        Tests that file is re-written correctly with new code.

        This test must ensure that original file is returned to previous state.
        Mocks won't work when making a subprocess call so make sure to delete all
        output files
        """
        expected_original_code = (
            'import requests\n\nrequests.get("www.google.com")\nvar = "hello"\n'
        )
        expected_new_code = 'import safe_requests\n\nsafe_requests.get("www.google.com")\nvar = "hello"\n'
        with open("tests/samples/make_request.py", "r", encoding="utf-8") as f:
            original_code = f.read()
        assert original_code == expected_original_code

        output_path = "test-output.txt"
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

        pathlib.Path(output_path).unlink(missing_ok=True)
