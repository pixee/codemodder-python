import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_url_sandbox import SemgrepUrlSandbox


class TestSemgrepUrlSandbox(BaseSASTCodemodTest):
    codemod = SemgrepUrlSandbox
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "url-sandbox"

    def test_url_sandbox(self, tmpdir):
        original_code = """\
        import requests
        from flask import Flask, request
        
        app = Flask(__name__)
        
        
        @app.route("/example")
        def example():
            url = request.args["url"]
            requests.get(url)
        """

        new_code = """\
        from flask import Flask, request
        from security import safe_requests

        app = Flask(__name__)
        
        
        @app.route("/example")
        def example():
            url = request.args["url"]
            safe_requests.get(url)
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "370059975f"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 22,
                                            "endLine": 10,
                                            "snippet": {
                                                "text": '    url = request.args["url"]\n    requests.get(url)'
                                            },
                                            "startColumn": 5,
                                            "startLine": 9,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Data from request object is passed to a new server-side request. This could lead to a server-side request forgery (SSRF). To mitigate, ensure that schemes and hosts are validated against an allowlist, do not forward the response to the user, and ensure proper authentication and transport-layer security in the proxied request. See https://owasp.org/www-community/attacks/Server_Side_Request_Forgery to learn more about SSRF vulnerabilities."
                            },
                            "properties": {},
                            "ruleId": "python.django.security.injection.ssrf.ssrf-injection-requests.ssrf-injection-requests",
                        },
                        {
                            "fingerprints": {"matchBasedId/v1": "cd899"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 22,
                                            "endLine": 10,
                                            "snippet": {
                                                "text": "    requests.get(url)"
                                            },
                                            "startColumn": 5,
                                            "startLine": 10,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Data from request object is passed to a new server-side request. This could lead to a server-side request forgery (SSRF). To mitigate, ensure that schemes and hosts are validated against an allowlist, do not forward the response to the user, and ensure proper authentication and transport-layer security in the proxied request."
                            },
                            "properties": {},
                            "ruleId": "python.flask.security.injection.ssrf-requests.ssrf-requests",
                        },
                    ],
                }
            ]
        }

        self.run_and_assert(
            tmpdir,
            original_code,
            new_code,
            results=json.dumps(results),
        )
