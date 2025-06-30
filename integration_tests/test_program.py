import subprocess
from pathlib import Path

import pytest
from sarif_pydantic.sarif import Run, Sarif, Tool, ToolDriver

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

    @pytest.mark.parametrize(
        "cli_args",
        [
            "--sonar-issues-json",
            "--sonar-hotspots-json",
            "--sonar-json",
        ],
    )
    def test_load_sast_only_by_sonar_flag(self, tmp_path, cli_args):
        tmp_file_path = tmp_path / "sonar.json"
        tmp_file_path.touch()
        completed_process = subprocess.run(
            [
                "codemodder",
                "tests/samples/",
                cli_args,
                f"{tmp_file_path}",
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        print(completed_process.stdout)
        print(completed_process.stderr)
        assert completed_process.returncode == 0
        assert RemoveAssertionInPytestRaises.id not in completed_process.stdout

    def test_load_sast_only_by_sarif_flag(self, tmp_path: Path):
        tmp_file_path = tmp_path / "sarif.json"
        sarif_run = Run(
            tool=Tool(driver=ToolDriver(name="test")),
            results=[],
        )
        sarif = Sarif(runs=[sarif_run], **{"$schema": ""})
        tmp_file_path.write_text(
            sarif.model_dump_json(indent=2, exclude_none=True, by_alias=True)
        )

        completed_process = subprocess.run(
            [
                "codemodder",
                "tests/samples/",
                "--sarif",
                f"{tmp_file_path}",
                "--dry-run",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed_process.returncode == 0
        assert RemoveAssertionInPytestRaises.id not in completed_process.stdout
