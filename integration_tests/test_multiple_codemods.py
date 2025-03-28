import json
import pathlib
import shutil
import subprocess

import pytest

from codemodder.codemods.test.integration_utils import SAMPLES_DIR


class TestMultipleCodemods:
    @pytest.mark.parametrize(
        "codemods",
        # In this particular case the order should not affect the result
        [
            "pixee:python/secure-random,pixee:python/fix-mutable-params",
            "pixee:python/fix-mutable-params,pixee:python/secure-random",
        ],
    )
    def test_two_codemods(self, codemods, tmpdir):
        source_file_name = "multiple_codemods.py"
        codetf_path = tmpdir / "codetf.txt"
        directory = tmpdir.mkdir("code")

        shutil.copy(pathlib.Path(SAMPLES_DIR) / source_file_name, directory)

        command = [
            "codemodder",
            directory,
            "--output",
            str(codetf_path),
            f"--codemod-include={codemods}",
            "--path-include",
            f"{source_file_name}",
            '--path-exclude=""',
        ]

        completed_process = subprocess.run(
            command,
            check=False,
            shell=False,
        )

        assert completed_process.returncode == 0

        with open(directory / source_file_name, "r", encoding="utf-8") as f:
            code = f.read()

        expected_code = """import secrets


def func(foo=None):
    foo = [] if foo is None else foo
    return secrets.SystemRandom().random()
"""

        assert code == expected_code

        with open(codetf_path, "r", encoding="utf-8") as f:
            results = json.load(f)

        ids = codemods.split(",")
        assert len(results["results"]) == 2
        # Order matters
        assert results["results"][0]["codemod"] == f"{ids[0]}"
        assert results["results"][1]["codemod"] == f"{ids[1]}"
