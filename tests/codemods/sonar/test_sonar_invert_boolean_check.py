import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_invert_boolean_check import SonarInvertedBooleanCheck


class TestSonarInvertedBooleanCheck(BaseSASTCodemodTest):
    codemod = SonarInvertedBooleanCheck
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "invert-boolean-check"

    def test_simple(self, tmpdir):
        input_code = """
        if not a == 2:
            b = not i < 10
        """
        expected_output = """
        if a != 2:
            b = i >= 10
        """
        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -1,3 +1,3 @@
 
-if not a == 2:
+if a != 2:
     b = not i < 10
""",
            """\
--- 
+++ 
@@ -1,3 +1,3 @@
 
 if not a == 2:
-    b = not i < 10
+    b = i >= 10
""",
        ]

        issues = {
            "issues": [
                {
                    "rule": "python:S1940",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 3,
                        "endOffset": 13,
                    },
                },
                {
                    "rule": "python:S1940",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 8,
                        "endOffset": 18,
                    },
                },
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            expected_diff_per_change,
            results=json.dumps(issues),
            num_changes=2,
        )
