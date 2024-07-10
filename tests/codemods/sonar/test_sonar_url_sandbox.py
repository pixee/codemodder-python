import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_url_sandbox import SonarUrlSandbox


class TestSonarUrlSandbox(BaseSASTCodemodTest):
    codemod = SonarUrlSandbox
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "url-sandbox"

    def test_simple(self, tmpdir):
        input_code = """
        import requests
        from flask import Flask, request
        
        app = Flask(__name__)
        
        
        @app.route("/example")
        def example():
            url = request.args["url"]
            requests.get(url)
        """
        expected = """
        from flask import Flask, request
        from security import safe_requests
        
        app = Flask(__name__)
        
        
        @app.route("/example")
        def example():
            url = request.args["url"]
            safe_requests.get(url)
        """
        issues = {
            "issues": [
                {
                    "rule": "pythonsecurity:S5144",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 11,
                        "endLine": 11,
                        "startOffset": 4,
                        "endOffset": 21,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
