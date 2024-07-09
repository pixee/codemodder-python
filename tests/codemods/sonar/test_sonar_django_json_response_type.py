import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_django_json_response_type import (
    SonarDjangoJsonResponseType,
)


class TestDjangoJsonResponseType(BaseSASTCodemodTest):
    codemod = SonarDjangoJsonResponseType
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "django-json-response-type"

    def test_simple(self, tmpdir):
        rule_id = "pythonsecurity:S5131"
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
                    "rule": rule_id,
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 7,
                        "endLine": 7,
                        "startOffset": 12,
                        "endOffset": 39,
                    },
                }
            ]
        }
        changes = self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues)
        )
        assert changes is not None
        assert changes[0].changes[0].findings is not None
        assert changes[0].changes[0].findings[0].id == rule_id
        assert changes[0].changes[0].findings[0].rule.id == rule_id
        assert changes[0].changes[0].findings[0].rule.name == rule_id
