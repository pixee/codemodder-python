import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_exception_without_raise import SonarExceptionWithoutRaise


class TestSonarExceptionWithoutRaise(BaseSASTCodemodTest):
    codemod = SonarExceptionWithoutRaise
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "exception-without-raise"

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
                    "component": "code.py",
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
