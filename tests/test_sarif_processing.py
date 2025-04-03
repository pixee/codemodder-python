import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError
from sarif_pydantic import Sarif

from codemodder.codemods.semgrep import process_semgrep_findings
from codemodder.sarifs import detect_sarif_tools
from codemodder.semgrep import SemgrepResult, SemgrepResultSet


class TestSarifProcessing:
    def test_extract_rule_id_codeql(self):
        sarif_file = Path("tests") / "samples" / "webgoat_v8.2.0_codeql.sarif"

        data = Sarif.model_validate_json(sarif_file.read_text())

        sarif_run = data.runs[0]
        assert sarif_run.results, "No results found in SARIF file"
        result = sarif_run.results[0]
        rule_id = SemgrepResult.extract_rule_id(
            result, sarif_run, truncate_rule_id=True
        )
        assert rule_id == "java/ssrf"

    def test_extract_rule_id_semgrep(self):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"

        data = Sarif.model_validate_json(sarif_file.read_text())

        sarif_run = data.runs[0]
        assert sarif_run.results, "No results found in SARIF file"
        result = sarif_run.results[0]
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
        assert isinstance(results["semgrep"][0], Path)

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
        assert completed_process.returncode == 0

    def test_two_sarifs_same_tool(self):
        results = detect_sarif_tools(
            [Path("tests/samples/webgoat_v8.2.0_codeql.sarif")] * 2
        )
        assert len(results) == 1
        assert len(results["codeql"]) == 2

    def test_bad_sarif(self, tmpdir, caplog):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"
        bad_json = tmpdir / "bad.sarif"
        with open(bad_json, "w") as f:
            # remove all { to make a badly formatted json
            f.write(sarif_file.read_text(encoding="utf-8").replace("{", ""))

        with pytest.raises(ValidationError):
            detect_sarif_tools([bad_json])
        assert f"Invalid SARIF file: {str(bad_json)}" in caplog.text

    def test_bad_sarif_no_runs_data(self, tmpdir, caplog):
        bad_json = tmpdir / "bad.sarif"
        data = """
            {
              "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json",
              "version": "2.1.0"
            }
        """
        with open(bad_json, "w") as f:
            f.write(data)

        with pytest.raises(ValidationError):
            detect_sarif_tools([bad_json])
        assert f"Invalid SARIF file: {str(bad_json)}" in caplog.text

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

    def test_stores_tools(self):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"
        result_set = process_semgrep_findings(tuple([str(sarif_file)]))
        assert result_set.tools
        assert result_set.tools[0]["driver"]["rules"]
