import json
from pathlib import Path
from unittest import TestCase, mock

from codemodder.codeql import CodeQLResultSet


class TestCodeQLResultSet(TestCase):

    def test_from_sarif(self):
        sarif_content = {
            "runs": [
                {
                    "tool": {
                        "driver": {"name": "CodeQL"},
                        "extensions": [
                            {
                                "rules": [
                                    {"id": "python/sql-injection"},
                                    {"id": "cs/web/missing-x-frame-options"},
                                ]
                            },
                        ],
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
                        },
                        {
                            "ruleId": "cs/web/missing-x-frame-options",
                            "message": {
                                "text": "Configuration file is missing the X-Frame-Options setting."
                            },
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "index": 5,
                                            "uri": "Web.config",
                                        }
                                    }
                                }
                            ],
                            "rule": {
                                "id": "cs/web/missing-x-frame-options",
                                "toolComponent": {"index": 0},
                                "index": 1,
                            },
                        },
                    ],
                }
            ]
        }
        sarif_file = Path("/path/to/sarif/file.sarif")
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=json.dumps(sarif_content))
        ):
            result_set = CodeQLResultSet.from_sarif(sarif_file)

            self.assertEqual(len(result_set), 2)
            self.assertIn("python/sql-injection", result_set)
            self.assertIn("cs/web/missing-x-frame-options", result_set)

            sql_result = result_set["python/sql-injection"]
            self.assertEqual(len(sql_result), 1)
            self.assertEqual(
                sql_result[Path("example.py")][0].rule_id,
                "python/sql-injection",
            )
            self.assertEqual(
                sql_result[Path("example.py")][0].locations[0].file,
                Path("example.py"),
            )
            self.assertEqual(
                sql_result[Path("example.py")][0].locations[0].start.line,
                10,
            )
            self.assertEqual(
                sql_result[Path("example.py")][0].locations[0].start.column,
                5,
            )
            self.assertEqual(
                sql_result[Path("example.py")][0].locations[0].end.line,
                10,
            )
            self.assertEqual(
                sql_result[Path("example.py")][0].locations[0].end.column,
                20,
            )

            xframe_result = result_set["cs/web/missing-x-frame-options"]
            self.assertEqual(len(xframe_result), 1)
            self.assertEqual(
                xframe_result[Path("Web.config")][0].rule_id,
                "cs/web/missing-x-frame-options",
            )
            self.assertEqual(
                xframe_result[Path("Web.config")][0].locations[0].file,
                Path("Web.config"),
            )
            self.assertEqual(
                xframe_result[Path("Web.config")][0].locations[0].start.line,
                0,
            )
            self.assertEqual(
                xframe_result[Path("Web.config")][0].locations[0].start.column,
                -1,
            )
            self.assertEqual(
                xframe_result[Path("Web.config")][0].locations[0].end.line,
                0,
            )
            self.assertEqual(
                xframe_result[Path("Web.config")][0].locations[0].end.column,
                -1,
            )
