import json
from pathlib import Path
from uuid import uuid4

from codemodder.semgrep import SemgrepResultSet
from core_codemods.sonar.results import SonarResultSet


class TestResults:

    def test_generated_urls(self, tmpdir):
        issues = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 2,
                        "endOffset": 2,
                    },
                },
                {
                    "rule": "pythonsecurity:S5147",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 19,
                        "endLine": 23,
                        "startOffset": 4,
                        "endOffset": 5,
                    },
                },
                {
                    "rule": "javascript:S6535",
                    "component": "pixee_bad-code:code.js",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 11,
                        "endOffset": 12,
                    },
                    "status": "OPEN",
                },
                {
                    "rule": "jssecurity:S2076",
                    "component": "pixee_bad-code:code.js",
                    "textRange": {
                        "startLine": 11,
                        "endLine": 11,
                        "startOffset": 4,
                        "endOffset": 8,
                    },
                    "status": "OPEN",
                },
                {
                    "status": "OPEN",
                    "rule": "typescript:S3504",
                    "component": "pixee_bad-code:code.ts",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 0,
                        "endOffset": 7,
                    },
                },
                {
                    "rule": "tssecurity:S2076",
                    "component": "pixee_bad-code:code.ts",
                    "textRange": {
                        "startLine": 11,
                        "endLine": 11,
                        "startOffset": 4,
                        "endOffset": 8,
                    },
                    "status": "OPEN",
                },
                {
                    "rule": "csharpsquid:S3878",
                    "component": "code.cs",
                    "line": 16,
                    "textRange": {
                        "startLine": 16,
                        "endLine": 16,
                        "startOffset": 40,
                        "endOffset": 53,
                    },
                    "flows": [],
                    "status": "OPEN",
                },
                {
                    "rule": "roslyn.sonaranalyzer.security.cs:S5131",
                    "status": "OPEN",
                    "component": "code.cs",
                    "textRange": {
                        "startLine": 10,
                        "endLine": 10,
                        "startOffset": 8,
                        "endOffset": 36,
                    },
                },
                {
                    "status": "OPEN",
                    "rule": "phpsecurity:S5131",
                    "component": "pixee_bad-code:code.php",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 4,
                        "endOffset": 33,
                    },
                },
            ]
        }
        sonar_json = Path(tmpdir) / "sonar_python.json"
        sonar_json.write_text(json.dumps(issues))

        result = SonarResultSet.from_json(sonar_json)
        assert (
            result.results_for_rules(["python:S5659"])[0].finding.rule.url
            == "https://rules.sonarsource.com/python/RSPEC-5659/"
        )
        assert (
            result.results_for_rules(["pythonsecurity:S5147"])[0].finding.rule.url
            == "https://rules.sonarsource.com/python/RSPEC-5147/"
        )

        assert (
            result.results_for_rules(["javascript:S6535"])[0].finding.rule.url
            == "https://rules.sonarsource.com/javascript/RSPEC-6535/"
        )
        assert (
            result.results_for_rules(["jssecurity:S2076"])[0].finding.rule.url
            == "https://rules.sonarsource.com/javascript/RSPEC-2076/"
        )

        assert (
            result.results_for_rules(["typescript:S3504"])[0].finding.rule.url
            == "https://rules.sonarsource.com/typescript/RSPEC-3504/"
        )
        assert (
            result.results_for_rules(["tssecurity:S2076"])[0].finding.rule.url
            == "https://rules.sonarsource.com/typescript/RSPEC-2076/"
        )

        assert (
            result.results_for_rules(["csharpsquid:S3878"])[0].finding.rule.url
            == "https://rules.sonarsource.com/dotnet/RSPEC-3878/"
        )
        assert (
            result.results_for_rules(["roslyn.sonaranalyzer.security.cs:S5131"])[
                0
            ].finding.rule.url
            == "https://rules.sonarsource.com/dotnet/RSPEC-5131/"
        )

        assert (
            result.results_for_rules(["phpsecurity:S5131"])[0].finding.rule.url
            == "https://rules.sonarsource.com/php/RSPEC-5131/"
        )

    def test_or(self, tmpdir):
        issues1 = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 2,
                        "endOffset": 2,
                    },
                }
            ]
        }
        issues2 = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 1,
                        "endOffset": 1,
                    },
                }
            ]
        }
        sonar_json1 = Path(tmpdir) / "sonar1.json"
        sonar_json1.write_text(json.dumps(issues1))
        sonar_json2 = Path(tmpdir) / "sonar2.json"
        sonar_json2.write_text(json.dumps(issues2))

        result1 = SonarResultSet.from_json(sonar_json1)
        result2 = SonarResultSet.from_json(sonar_json2)

        combined = result1 | result2
        assert len(combined["python:S5659"][Path("code.py")]) == 2
        assert (
            result2["python:S5659"][Path("code.py")][0]
            in combined["python:S5659"][Path("code.py")]
        )
        assert (
            result1["python:S5659"][Path("code.py")][0]
            in combined["python:S5659"][Path("code.py")]
        )

        assert combined.results_for_rules(["python:S5659"]) == [
            result1["python:S5659"][Path("code.py")][0],
            result2["python:S5659"][Path("code.py")][0],
        ]

    def test_sonar_flows(self, tmpdir):
        issues = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 13,
                        "endOffset": 14,
                    },
                    "component": "code.py",
                    "flows": [
                        {
                            "locations": [
                                {
                                    "component": "code.py",
                                    "textRange": {
                                        "startLine": 1,
                                        "endLine": 1,
                                        "startOffset": 8,
                                        "endOffset": 9,
                                    },
                                }
                            ]
                        }
                    ],
                    "status": "OPEN",
                },
            ],
        }

        sonar_json1 = Path(tmpdir) / "sonar1.json"
        sonar_json1.write_text(json.dumps(issues))

        resultset = SonarResultSet.from_json(sonar_json1)
        result = resultset["python:S5659"][Path("code.py")][0]
        assert result.codeflows
        assert result.codeflows[0]
        assert result.codeflows[0][0].start.line == 1
        assert result.codeflows[0][0].start.column == 8
        assert result.codeflows[0][0].end.line == 1
        assert result.codeflows[0][0].end.column == 9

    def test_sonar_robustness(self, tmpdir):
        sonar_json = Path(tmpdir) / "sonar1.json"
        # not a valid json
        sonar_json.touch()
        result = SonarResultSet.from_json(sonar_json)
        # did not crash and returned an empty ResultSet
        assert not result

    def test_sonar_result_by_finding_id(self, tmpdir):
        issues = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 2,
                        "endOffset": 2,
                    },
                    "key": "1234",
                }
            ]
        }
        sonar_json = Path(tmpdir) / "sonar1.json"
        sonar_json.write_text(json.dumps(issues))

        result_set = SonarResultSet.from_json(sonar_json)
        result = result_set.result_by_finding_id("1234")
        assert result is not None
        assert result.finding.rule.id == "python:S5659"

    def test_semgrep_sarif_result_by_finding_id(self, tmpdir):
        uuid = str(uuid4())
        issues = {
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Semgrep",
                            "version": "0.100.0",
                        }
                    },
                    "results": [
                        {
                            "message": {
                                "text": "Found a potential issue",
                            },
                            "guid": uuid,
                            "ruleId": "python:fake.rule.name",
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": str(Path(tmpdir) / "code.py"),
                                        },
                                        "region": {
                                            "startLine": 2,
                                            "startColumn": 2,
                                        },
                                    }
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        sarif_json = Path(tmpdir) / "semgrep.sarif"
        sarif_json.write_text(json.dumps(issues))

        result_set = SemgrepResultSet.from_sarif(sarif_json)
        result = result_set.result_by_finding_id(uuid)
        assert result is not None
        assert result.finding.rule.id == "python:fake.rule.name"
