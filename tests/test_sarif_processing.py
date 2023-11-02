from codemodder.sarifs import extract_rule_id
from codemodder.sarifs import SarifResultSet
from pathlib import Path
import subprocess
import json


class TestSarifProcessing:
    def test_extract_rule_id_codeql(self):
        sarif_file = Path("tests") / "samples" / "webgoat_v8.2.0_codeql.sarif"

        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        sarif_run = data["runs"][0]
        result = sarif_run["results"][0]
        rule_id = extract_rule_id(result, sarif_run)
        assert rule_id == "java/ssrf"

    def test_extract_rule_id_semgrep(self):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"

        with open(sarif_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        sarif_run = data["runs"][0]
        result = sarif_run["results"][0]
        rule_id = extract_rule_id(result, sarif_run)
        assert rule_id == "secure-random"

    def test_results_by_rule_id(self):
        sarif_file = Path("tests") / "samples" / "semgrep.sarif"

        results = SarifResultSet.from_sarif(sarif_file)
        expected_rule = "secure-random"
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
                "secure-random",
                "--dry-run",
            ],
            check=False,
        )
        assert completed_process.returncode == 0
