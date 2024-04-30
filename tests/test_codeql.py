import json
from pathlib import Path
from unittest import TestCase, mock

from codemodder.codeql import CodeQLResultSet


class TestCodeQLResultSet(TestCase):

    def test_from_sarif(self):
        # Given a SARIF file with known content
        sarif_content = {
            "runs": [
                {
                    "tool": {
                        "driver": {"name": "CodeQL"},
                        "extensions": [{"rules": [{"id": "python/sql-injection"}]}],
                    },
                    "results": [
                        {
                            "ruleId": "python/sql-injection",
                            "message": {"text": "Possible SQL injection"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "example.py"},
                                        "region": {
                                            "startLine": 10,
                                            "startColumn": 5,
                                            "endLine": 10,
                                            "endColumn": 20,
                                        },
                                    }
                                }
                            ],
                            "rule": {
                                "toolComponent": {"index": 0},
                                "index": 0,
                            },
                        }
                    ],
                }
            ]
        }
        sarif_file = Path("/path/to/sarif/file.sarif")
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=json.dumps(sarif_content))
        ):
            # When parsing the SARIF file
            result_set = CodeQLResultSet.from_sarif(sarif_file)

            # Then the result set should contain the expected results
            self.assertEqual(len(result_set), 1)
            self.assertIn("python/sql-injection", result_set)
            self.assertEqual(len(result_set["python/sql-injection"]), 1)
            self.assertEqual(
                result_set["python/sql-injection"][Path("example.py")][0].rule_id,
                "python/sql-injection",
            )
            self.assertEqual(
                result_set["python/sql-injection"][Path("example.py")][0]
                .locations[0]
                .file,
                Path("example.py"),
            )
            self.assertEqual(
                result_set["python/sql-injection"][Path("example.py")][0]
                .locations[0]
                .start.line,
                10,
            )
            self.assertEqual(
                result_set["python/sql-injection"][Path("example.py")][0]
                .locations[0]
                .start.column,
                5,
            )
            self.assertEqual(
                result_set["python/sql-injection"][Path("example.py")][0]
                .locations[0]
                .end.line,
                10,
            )
            self.assertEqual(
                result_set["python/sql-injection"][Path("example.py")][0]
                .locations[0]
                .end.column,
                20,
            )
