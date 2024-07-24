import json
import subprocess
from pathlib import Path

import pytest

from codemodder.sarifs import DuplicateToolError, detect_sarif_tools
from codemodder.semgrep import SemgrepResult, SemgrepResultSet


class TestSarifProcessing:
    def test_extract_rule_id_codeql(self):
        sarif_file = Path("tests") / "samples" / "webgoat_v8.2.0_codeql.sarif"

        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        sarif_run = data["runs"][0]
        result = sarif_run["results"][0]
        rule_id = SemgrepResult.extract_rule_id(
            result, sarif_run, truncate_rule_id=True
        )
        assert rule_id == "java/ssrf"

    def test_extract_rule_id_semgrep(self):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"

        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        sarif_run = data["runs"][0]
        result = sarif_run["results"][0]
        rule_id = SemgrepResult.extract_rule_id(
            result, sarif_run, truncate_rule_id=True
        )
        assert rule_id == "secure-random"

    def test_detect_sarif_with_bom_encoding(self, tmpdir):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"
        sarif_file_bom = tmpdir / "semgrep_bom.sarif"

        with open(sarif_file_bom, "w") as f:
            f.write("\ufeff")
            f.write(sarif_file.read_text(encoding="utf-8"))

        results = detect_sarif_tools([sarif_file_bom])
        assert len(results) == 1

    @pytest.mark.parametrize("truncate", [True, False])
    def test_results_by_rule_id(self, truncate):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"

        results = SemgrepResultSet.from_sarif(sarif_file, truncate_rule_id=truncate)
        expected_rule = (
            "secure-random" if truncate else "codemodder.codemods.semgrep.secure-random"
        )
        assert list(results.keys()) == [expected_rule]

        expected_path = Path("tests/samples/insecure_random.py")
        assert list(results[expected_rule].keys()) == [expected_path]

        assert results[expected_rule][expected_path][0].rule_id == expected_rule
        assert (
            results[expected_rule][expected_path][0].locations[0].file == expected_path
        )

    def test_codeql_sarif_input(self, tmpdir):
        completed_process = subprocess.run(
            [
                "codemodder",
                "tests/samples/",
                "--sarif",
                "tests/samples/webgoat_v8.2.0_codeql.sarif",
                "--output",
                tmpdir / "doesntmatter.txt",
                "--codemod-include",
                "pixee:python/secure-random",
                "--dry-run",
            ],
            check=False,
        )
        assert completed_process.returncode == 0

    def test_codeql_sarif_input_two_sarifs_same_tool(self, tmpdir):
        tmpfile = Path(tmpdir) / "doesntmatter.sarif"
        codeql_sarif = Path("tests/samples/webgoat_v8.2.0_codeql.sarif")
        tmpfile.write_text(codeql_sarif.read_text())

        completed_process = subprocess.run(
            [
                "codemodder",
                "tests/samples/",
                "--sarif",
                f"{codeql_sarif},{tmpfile}",
                "--output",
                tmpdir / "doesntmatter.txt",
                "--codemod-include",
                "pixee:python/secure-random",
                "--dry-run",
            ],
            check=False,
            capture_output=True,
        )
        assert completed_process.returncode == 1
        assert (
            "duplicate tool sarif detected: codeql" in completed_process.stderr.decode()
        )

    def test_two_sarifs_same_tool(self):
        with pytest.raises(DuplicateToolError) as exc:
            detect_sarif_tools([Path("tests/samples/webgoat_v8.2.0_codeql.sarif")] * 2)
        assert "duplicate tool sarif detected: codeql" in str(exc.value)

    def test_two_sarifs_different_tools(self):
        results = detect_sarif_tools(
            [
                Path("tests/samples/webgoat_v8.2.0_codeql.sarif"),
                Path("tests/samples/semgrep.sarif"),
            ]
        )
        assert len(results) == 2
        assert "codeql" in results
        assert "semgrep" in results
        assert len(results["codeql"]) == 1
        assert len(results["semgrep"]) == 1
