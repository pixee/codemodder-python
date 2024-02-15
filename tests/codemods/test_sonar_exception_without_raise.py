import json
from core_codemods.sonar.sonar_exception_without_raise import SonarExceptionWithoutRaise
from tests.codemods.base_codemod_test import BaseSASTCodemodTest


class TestSonarExceptionWithoutRaise(BaseSASTCodemodTest):
    codemod = SonarExceptionWithoutRaise
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "exception-without-raise-S3984"

    def test_simple(self, tmpdir):
        input_code = """
        ValueError
        """
        expected = """
        raise ValueError
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S3984",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 1,
                        "endOffset": 10,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
