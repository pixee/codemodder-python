import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_django_secure_set_cookie import (
    SemgrepDjangoSecureSetCookie,
)


class TestSemgrepDjangoSecureSetCookie(BaseSASTCodemodTest):
    codemod = SemgrepDjangoSecureSetCookie
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "django-secure-set-cookie"

    def test_import(self, tmpdir):
        input_code = """\
        from django.shortcuts import render


        def index(request, template):
            response = render(request, template)
            response.set_cookie("name", "value")
        
            return response
        """
        expected_output = """\
        from django.shortcuts import render


        def index(request, template):
            response = render(request, template)
            response.set_cookie("name", "value", secure=True, httponly=True, samesite='Lax')
        
            return response
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
                                            "endColumn": 41,
                                            "endLine": 6,
                                            "snippet": {
                                                "text": '    response.set_cookie("name", "value")'
                                            },
                                            "startColumn": 5,
                                            "startLine": 6,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Django cookies should be handled securely by setting secure=True, httponly=True, and samesite='Lax' in response.set_cookie(...). If your situation calls for different settings, explicitly disable the setting. If you want to send the cookie over http, set secure=False. If you want to let client-side JavaScript read the cookie, set httponly=False. If you want to attach cookies to requests for external sites, set samesite=None."
                            },
                            "properties": {},
                            "ruleId": "python.django.security.audit.secure-cookies.django-secure-set-cookie",
                        }
                    ]
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(results),
        )
