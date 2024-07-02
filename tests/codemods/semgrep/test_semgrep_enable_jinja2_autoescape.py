import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_enable_jinja2_autoescape import (
    SemgrepEnableJinja2Autoescape,
)


class TestEnableJinja2Autoescape(BaseSASTCodemodTest):
    codemod = SemgrepEnableJinja2Autoescape
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "enable-jinja2-autoescape"

    def test_import(self, tmpdir):
        input_code = """
        import jinja2
        env = jinja2.Environment()
        var = "hello"
        """
        expexted_output = """
        import jinja2
        env = jinja2.Environment(autoescape=True)
        var = "hello"
        """
        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 27,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "env = jinja2.Environment()"
                                            },
                                            "startColumn": 7,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected direct use of jinja2. If not done properly, this may bypass HTML escaping which opens up the application to cross-site scripting (XSS) vulnerabilities. Prefer using the Flask method 'render_template()' and templates with a '.html' extension in order to prevent XSS."
                            },
                            "properties": {},
                            "ruleId": "python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2",
                        }
                    ]
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expexted_output,
            results=json.dumps(results),
        )
