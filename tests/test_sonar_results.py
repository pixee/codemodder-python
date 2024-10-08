from core_codemods.sonar.results import SonarResult


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
    assert sonar_result.locations == []
    assert sonar_result.codeflows == []
