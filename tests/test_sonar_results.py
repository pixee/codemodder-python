import json
from pathlib import Path

from core_codemods.sonar.results import SonarResult, SonarResultSet

SAMPLE_DIR = Path(__file__).parent / "samples"


def test_result_without_textrange():
    result = {
        "cleanCodeAttribute": "FORMATTED",
        "cleanCodeAttributeCategory": "CONSISTENT",
        "component": "PixeeSandbox_DVWA:vulnerabilities/exec/help/help.php",
        "creationDate": "2020-10-21T16:03:39+0200",
        "debt": "2min",
        "effort": "2min",
        "flows": [],
        "impacts": [{"severity": "LOW", "softwareQuality": "MAINTAINABILITY"}],
        "issueStatus": "OPEN",
        "key": "AZJnP4pZPJb5bI8DP25Y",
        "message": "Replace all tab characters in this file by sequences of "
        "white-spaces.",
        "organization": "pixee-sandbox",
        "project": "PixeeSandbox_DVWA",
        "rule": "php:S105",
        "severity": "MINOR",
        "status": "OPEN",
        "tags": ["convention", "psr2"],
        "type": "CODE_SMELL",
        "updateDate": "2024-10-07T15:50:36+0200",
    }
    sonar_result = SonarResult.from_result(result)
    assert sonar_result.rule_id == "php:S105"
    assert sonar_result.finding_id == "AZJnP4pZPJb5bI8DP25Y"
    assert sonar_result.locations == ()
    assert sonar_result.codeflows == ()


def test_parse_issues_json():
    results = SonarResultSet.from_json(SAMPLE_DIR / "sonar_issues.json")
    assert len(results) == 34


def test_parse_hotspots_json():
    results = SonarResultSet.from_json(SAMPLE_DIR / "sonar_hotspots.json")
    assert len(results) == 5


def test_combined_json(tmpdir):
    issues = json.loads(SAMPLE_DIR.joinpath("sonar_issues.json").read_text())
    hotspots = json.loads(SAMPLE_DIR.joinpath("sonar_hotspots.json").read_text())
    Path(tmpdir).joinpath("combined.json").write_text(
        json.dumps({"issues": issues["issues"] + hotspots["hotspots"]})
    )

    results = SonarResultSet.from_json(Path(tmpdir).joinpath("combined.json"))
    assert len(results) == 39


def test_empty_issues(tmpdir, caplog):
    empty_json = tmpdir / "empty.json"
    empty_json.write_text('{"issues": []}', encoding="utf-8")

    results = SonarResultSet.from_json(empty_json)

    assert len(results) == 0
    assert "Could not parse sonar json" not in caplog.text


def test_empty_hotspots(tmpdir, caplog):
    empty_json = tmpdir / "empty.json"
    empty_json.write_text('{"hotspots": []}', encoding="utf-8")

    results = SonarResultSet.from_json(empty_json)

    assert len(results) == 0
    assert "Could not parse sonar json" not in caplog.text
