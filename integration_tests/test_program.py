import subprocess

from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)


class TestProgramFails:
    def test_no_project_dir_provided(self):
        completed_process = subprocess.run(["codemodder"], check=False)
        assert completed_process.returncode == 3

    def test_codemods_include_exclude_conflict(self):
        completed_process = subprocess.run(
            [
                "codemodder",
                "some/path",
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
        completed_process = subprocess.run(
            [
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
