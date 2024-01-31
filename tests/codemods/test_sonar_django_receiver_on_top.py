import json
from core_codemods.sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop
from tests.codemods.base_codemod_test import BaseSASTCodemodTest
from textwrap import dedent


class TestSonarDjangoReceiverOnTop(BaseSASTCodemodTest):
    codemod = SonarDjangoReceiverOnTop
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "django-receiver-on-top-S6552"

    def test_simple(self, tmpdir):
        input_code = """\
        from django.dispatch import receiver

        @csrf_exempt
        @receiver(request_finished)
        def foo():
            pass
        """
        expected = """\
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
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 4,
                        "endLine": 4,
                        "startOffset": 1,
                        "endOffset": 27,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir, dedent(input_code), dedent(expected), results=json.dumps(issues)
        )
