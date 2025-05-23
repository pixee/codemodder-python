import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_fix_missing_self_or_cls import SonarFixMissingSelfOrCls


class TestSonarFixMissingSelfOrCls(BaseSASTCodemodTest):
    codemod = SonarFixMissingSelfOrCls
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "fix-missing-self-or-cls"

    def test_simple(self, tmpdir):
        input_code = """
        class A:
            def instance_method():
                pass
            
            @classmethod
            def class_method():
                pass
        """
        expected_output = """
        class A:
            def instance_method(self):
                pass
            
            @classmethod
            def class_method(cls):
                pass
        """
        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -1,6 +1,6 @@
 
 class A:
-    def instance_method():
+    def instance_method(self):
         pass
 
     @classmethod
""",
            """\
--- 
+++ 
@@ -4,5 +4,5 @@
         pass
 
     @classmethod
-    def class_method():
+    def class_method(cls):
         pass
""",
        ]

        issues = {
            "issues": [
                {
                    "rule": "python:S5719",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 4,
                        "endOffset": 25,
                    },
                },
                {
                    "rule": "python:S5719",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 7,
                        "endLine": 7,
                        "startOffset": 4,
                        "endOffset": 22,
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
