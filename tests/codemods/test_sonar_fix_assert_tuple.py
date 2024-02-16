import json
from core_codemods.sonar.sonar_fix_assert_tuple import SonarFixAssertTuple
from tests.codemods.base_codemod_test import BaseSASTCodemodTest


class TestSonarFixAssertTuple(BaseSASTCodemodTest):
    codemod = SonarFixAssertTuple
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "fix-assert-tuple-S5905"

    def test_simple(self, tmpdir):
        input_code = """
        assert (1,2,3)
        """
        expected_output = """
        assert 1
        assert 2
        assert 3
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5905",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 8,
                        "endOffset": 15,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(issues),
            num_changes=3,
        )
