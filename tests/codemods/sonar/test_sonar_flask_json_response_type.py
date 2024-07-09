import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_flask_json_response_type import (
    SonarFlaskJsonResponseType,
)


class TestSonarFlaskJsonResponseType(BaseSASTCodemodTest):
    codemod = SonarFlaskJsonResponseType
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "flask-json-response-type"

    def test_simple(self, tmpdir):
        input_code = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response)
        """
        expected = """
        from flask import make_response, Flask
        import json

        app = Flask(__name__)

        @app.route("/test")
        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return make_response(json_response, {'Content-Type': 'application/json'})
        """
        issues = {
            "issues": [
                {
                    "rule": "pythonsecurity:S5131",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 10,
                        "endLine": 10,
                        "startOffset": 11,
                        "endOffset": 39,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
