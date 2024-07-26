import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop


class TestSonarDjangoReceiverOnTop(BaseSASTCodemodTest):
    codemod = SonarDjangoReceiverOnTop
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "django-receiver-on-top"

    def assert_findings(self, changes):
        # For now we can only link the finding to the line with the receiver decorator
        assert changes[0].findings
        assert not changes[1].findings

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
                    "component": "code.py",
                    "textRange": {
                        "startLine": 5,
                        "endLine": 5,
                        "startOffset": 1,
                        "endOffset": 27,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues), num_changes=2
        )
