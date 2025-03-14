import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_enable_jinja2_autoescape import (
    SonarEnableJinja2Autoescape,
)


class TestEnableJinja2Autoescape(BaseSASTCodemodTest):
    codemod = SonarEnableJinja2Autoescape
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "enable-jinja2-autoescape"

    def test_simple(self, tmpdir):
        input_code = """
        from jinja2 import Environment
        env = Environment()
        env = Environment(autoescape=False)
        """
        expected_output = """
        from jinja2 import Environment
        env = Environment(autoescape=True)
        env = Environment(autoescape=True)
        """
        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -1,4 +1,4 @@
 
 from jinja2 import Environment
-env = Environment()
+env = Environment(autoescape=True)
 env = Environment(autoescape=False)
""",
            """\
--- 
+++ 
@@ -1,4 +1,4 @@
 
 from jinja2 import Environment
 env = Environment()
-env = Environment(autoescape=False)
+env = Environment(autoescape=True)
""",
        ]

        hotspots = {
            "hotspots": [
                {
                    "rule": "python:S5247",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 6,
                        "endOffset": 19,
                    },
                },
                {
                    "rule": "python:S5247",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 4,
                        "endLine": 4,
                        "startOffset": 6,
                        "endOffset": 35,
                    },
                },
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            expected_diff_per_change,
            results=json.dumps(hotspots),
            num_changes=2,
        )
