import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_timezone_aware_datetime import SonarTimezoneAwareDatetime


class TestSonarTimezoneAwareDatetime(BaseSASTCodemodTest):
    codemod = SonarTimezoneAwareDatetime
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "timezone-aware-datetime"

    def test_simple(self, tmpdir):
        input_code = """\
        import datetime
        
        datetime.datetime.utcnow()
        timestamp = 1571595618.0
        datetime.datetime.utcfromtimestamp(timestamp)
        """
        expected = """\
        import datetime
        
        datetime.datetime.now(tz=datetime.timezone.utc)
        timestamp = 1571595618.0
        datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        """
        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -1,5 +1,5 @@
 import datetime
 
-datetime.datetime.utcnow()
+datetime.datetime.now(tz=datetime.timezone.utc)
 timestamp = 1571595618.0
 datetime.datetime.utcfromtimestamp(timestamp)
""",
            """\
--- 
+++ 
@@ -2,4 +2,4 @@
 
 datetime.datetime.utcnow()
 timestamp = 1571595618.0
-datetime.datetime.utcfromtimestamp(timestamp)
+datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
""",
        ]

        issues = {
            "issues": [
                {
                    "key": "AZFcGzHT5VEY3NanjlD7",
                    "rule": "python:S6903",
                    "severity": "MAJOR",
                    "component": "code.py",
                    "hash": "92aca3da1e08f944a3c408df27c54b28",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 0,
                        "endOffset": 26,
                    },
                    "status": "OPEN",
                    "message": "Don't use `datetime.datetime.utcnow` to create this datetime object.",
                },
                {
                    "key": "AZFcGzHT5VEY3NanjlD8",
                    "rule": "python:S6903",
                    "severity": "MAJOR",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 5,
                        "endLine": 5,
                        "startOffset": 0,
                        "endOffset": 45,
                    },
                    "status": "OPEN",
                    "message": "Don't use `datetime.datetime.utcfromtimestamp` to create this datetime object.",
                },
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            expected_diff_per_change,
            results=json.dumps(issues),
            num_changes=2,
        )
