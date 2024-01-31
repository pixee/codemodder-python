import json
from core_codemods.sonar.sonar_exception_without_raise import SonarExceptionWithoutRaise
from tests.codemods.base_codemod_test import BaseSASTCodemodTest
from textwrap import dedent


class TestSonarExceptionWithoutRaise(BaseSASTCodemodTest):
    codemod = SonarExceptionWithoutRaise
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "exception-without-raise-S3984"

    def test_simple(self, tmpdir):
        input_code = """\
        ValueError
        """
        expected = """\
        raise ValueError
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S3984",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 1,
                        "endOffset": 10,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir, dedent(input_code), dedent(expected), results=json.dumps(issues)
        )
