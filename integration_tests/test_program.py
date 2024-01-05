import subprocess
from security import safe_command


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
