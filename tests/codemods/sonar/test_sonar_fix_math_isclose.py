import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_fix_math_isclose import SonarFixMathIsClose


class TestSonarFixMathIsClose(BaseSASTCodemodTest):
    codemod = SonarFixMathIsClose
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "fix-math-isclose"

    def test_simple(self, tmpdir):
        input_code = """
        import math        
        
        def foo(a):
            return math.isclose(a, 0)
        """
        expected_output = """
        import math        
        
        def foo(a):
            return math.isclose(a, 0, abs_tol=1e-09)
        """
        hotspots = {
            "issues": [
                {
                    "rule": "python:S6727",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 5,
                        "endLine": 5,
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
            results=json.dumps(hotspots),
            num_changes=1,
        )
