import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_secure_cookie import SonarSecureCookie


class TestSonarSecureCookie(BaseSASTCodemodTest):
    codemod = SonarSecureCookie
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "secure-cookie"

    def test_simple(self, tmpdir):
        input_code = """
        import flask

        response = flask.make_response()
        var = "hello"
        response.set_cookie("name", "value")

        response2 = flask.Response()
        var = "hello"
        response2.set_cookie("name", "value")
        """
        expected = """
        import flask

        response = flask.make_response()
        var = "hello"
        response.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')

        response2 = flask.Response()
        var = "hello"
        response2.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        """
        issues = {
            "hotspots": [
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 6,
                        "endLine": 6,
                        "startOffset": 0,
                        "endOffset": 19,
                    },
                    "ruleKey": "python:S2092",
                },
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 10,
                        "endLine": 10,
                        "startOffset": 0,
                        "endOffset": 20,
                    },
                    "ruleKey": "python:S2092",
                },
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 6,
                        "endLine": 6,
                        "startOffset": 0,
                        "endOffset": 19,
                    },
                    "ruleKey": "python:S3330",
                },
                {
                    "component": "code.py",
                    "status": "TO_REVIEW",
                    "textRange": {
                        "startLine": 10,
                        "endLine": 10,
                        "startOffset": 0,
                        "endOffset": 20,
                    },
                    "ruleKey": "python:S3330",
                },
            ],
        }
        self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues), num_changes=2
        )
