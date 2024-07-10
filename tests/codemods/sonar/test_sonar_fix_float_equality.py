import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_fix_float_equality import SonarFixFloatEquality


class TestSonarFixFloatEquality(BaseSASTCodemodTest):
    codemod = SonarFixFloatEquality
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "fix-float-equality"

    def test_simple(self, tmpdir):
        input_code = """
        def foo(a, b):
            return a == b - 0.1
        """
        expected_output = """
        import math
        
        def foo(a, b):
            return math.isclose(a, b - 0.1, rel_tol=1e-09, abs_tol=0.0)
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S1244",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 3,
                        "endLine": 3,
                        "startOffset": 11,
                        "endOffset": 23,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(issues),
        )
