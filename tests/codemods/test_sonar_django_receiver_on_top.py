import json
from core_codemods.sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop
from tests.codemods.base_codemod_test import BaseSASTCodemodTest


class TestSonarDjangoReceiverOnTop(BaseSASTCodemodTest):
    codemod = SonarDjangoReceiverOnTop
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "django-receiver-on-top-S6552"

    def test_simple(self, tmpdir):
        input_code = """
        from django.dispatch import receiver

        @csrf_exempt
        @receiver(request_finished)
        def foo():
            pass
        """
        expected = """
        from django.dispatch import receiver

        @receiver(request_finished)
        @csrf_exempt
        def foo():
            pass
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S6552",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 5,
                        "endLine": 5,
                        "startOffset": 1,
                        "endOffset": 27,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
