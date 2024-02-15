import json
from core_codemods.sonar.sonar_django_json_response_type import (
    SonarDjangoJsonResponseType,
)
from tests.codemods.base_codemod_test import BaseSASTCodemodTest


class TestDjangoJsonResponseType(BaseSASTCodemodTest):
    codemod = SonarDjangoJsonResponseType
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "django-json-response-type-S5131"

    def test_simple(self, tmpdir):
        input_code = """
        from django.http import HttpResponse
        import json

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return HttpResponse(json_response)
        """
        expected = """
        from django.http import HttpResponse
        import json

        def foo(request):
            json_response = json.dumps({ "user_input": request.GET.get("input") })
            return HttpResponse(json_response, content_type="application/json")
        """
        issues = {
            "issues": [
                {
                    "rule": "pythonsecurity:S5131",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 7,
                        "endLine": 7,
                        "startOffset": 12,
                        "endOffset": 39,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
