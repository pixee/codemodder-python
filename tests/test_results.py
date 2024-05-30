import json
from pathlib import Path

from core_codemods.sonar.results import SonarResultSet


class TestResults:
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

    def test_sonar_only_open_issues(self, tmpdir):
        issues = {
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
                },
                {
                    "rule": "python:S5659",
                    "status": "RESOLVED",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 1,
                        "endOffset": 1,
                    },
                },
            ]
        }
        sonar_json1 = Path(tmpdir) / "sonar1.json"
        sonar_json1.write_text(json.dumps(issues))

        result = SonarResultSet.from_json(sonar_json1)
        assert len(result["python:S5659"][Path("code.py")]) == 1

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
