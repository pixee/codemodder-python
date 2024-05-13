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
                                    {"id": "cs/web/xss"},
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
                        {
                            "codeFlows": [
                                {
                                    "threadFlows": [
                                        {
                                            "locations": [
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "access to property QueryString : NameValueCollection"
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 48,
                                                                "endLine": 33,
                                                                "startColumn": 29,
                                                                "startLine": 33,
                                                            },
                                                        },
                                                    }
                                                },
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "access to local variable filename : String"
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 26,
                                                                "endLine": 33,
                                                                "startColumn": 18,
                                                                "startLine": 33,
                                                            },
                                                        },
                                                    }
                                                },
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "... + ..."
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 71,
                                                                "endLine": 43,
                                                                "startColumn": 42,
                                                                "startLine": 43,
                                                            },
                                                        },
                                                    }
                                                },
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "threadFlows": [
                                        {
                                            "locations": [
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "access to property QueryString : NameValueCollection"
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 48,
                                                                "endLine": 33,
                                                                "startColumn": 29,
                                                                "startLine": 33,
                                                            },
                                                        },
                                                    }
                                                },
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "access to indexer : String"
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 60,
                                                                "endLine": 33,
                                                                "startColumn": 29,
                                                                "startLine": 33,
                                                            },
                                                        },
                                                    }
                                                },
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "access to local variable filename : String"
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 26,
                                                                "endLine": 33,
                                                                "startColumn": 18,
                                                                "startLine": 33,
                                                            },
                                                        },
                                                    }
                                                },
                                                {
                                                    "location": {
                                                        "message": {
                                                            "text": "... + ..."
                                                        },
                                                        "physicalLocation": {
                                                            "artifactLocation": {
                                                                "index": 8,
                                                                "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                                            },
                                                            "region": {
                                                                "endColumn": 71,
                                                                "endLine": 43,
                                                                "startColumn": 42,
                                                                "startLine": 43,
                                                            },
                                                        },
                                                    }
                                                },
                                            ]
                                        }
                                    ]
                                },
                            ],
                            "correlationGuid": "d42b86b5-c4da-4af1-8c5b-5d0b83a34cb3",
                            "level": "error",
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "index": 8,
                                            "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                        },
                                        "region": {
                                            "endColumn": 71,
                                            "endLine": 43,
                                            "startColumn": 42,
                                            "startLine": 43,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "[User-provided value](1) flows to here and is written to HTML or JavaScript."
                            },
                            "partialFingerprints": {
                                "primaryLocationLineHash": "f6cad8bc4c77c3d9:1"
                            },
                            "properties": {
                                "github/alertNumber": 8,
                                "github/alertUrl": "https://api.github.com/repos/pixee/ClassicWebGoat.NET/code-scanning/alerts/8",
                            },
                            "relatedLocations": [
                                {
                                    "id": 1,
                                    "message": {"text": "User-provided value"},
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "index": 0,
                                            "uri": "WebGoat/Content/PathManipulation.aspx.cs",
                                        },
                                        "region": {
                                            "endColumn": 48,
                                            "endLine": 33,
                                            "startColumn": 29,
                                            "startLine": 33,
                                        },
                                    },
                                }
                            ],
                            "rule": {
                                "id": "cs/web/xss",
                                "toolComponent": {"index": 0},
                                "index": 2,
                            },
                            "ruleId": "cs/web/xss",
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

            self.assertEqual(len(result_set), 3)
            self.assertIn("python/sql-injection", result_set)
            self.assertIn("cs/web/missing-x-frame-options", result_set)
            self.assertIn("cs/web/xss", result_set)

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

            xss_result = result_set["cs/web/xss"]
            self.assertEqual(len(xss_result), 1)
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0].rule_id,
                "cs/web/xss",
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .locations[0]
                .file,
                Path("WebGoat/Content/PathManipulation.aspx.cs"),
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .locations[0]
                .start.line,
                43,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .locations[0]
                .start.column,
                42,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .locations[0]
                .end.line,
                43,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .locations[0]
                .end.column,
                71,
            )

            # codeflows
            self.assertEqual(
                len(
                    xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][
                        0
                    ].codeflows
                ),
                2,
            )
            self.assertEqual(
                len(
                    xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][
                        0
                    ].codeflows[0]
                ),
                3,
            )
            self.assertEqual(
                len(
                    xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][
                        0
                    ].codeflows[1]
                ),
                4,
            )

            # related locations
            self.assertEqual(
                len(
                    xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][
                        0
                    ].related_locations
                ),
                1,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .related_locations[0]
                .message,
                "User-provided value",
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .related_locations[0]
                .location.start.line,
                33,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .related_locations[0]
                .location.start.column,
                29,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .related_locations[0]
                .location.end.line,
                33,
            )
            self.assertEqual(
                xss_result[Path("WebGoat/Content/PathManipulation.aspx.cs")][0]
                .related_locations[0]
                .location.end.column,
                48,
            )
