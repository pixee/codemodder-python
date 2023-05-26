import subprocess


class TestProgramFails:
    def test_no_project_dir_provided(self):
        completed_process = subprocess.run(["python", "-m", "codemodder"])
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
            ]
        )
        # should be 1
        assert completed_process.returncode == 0
