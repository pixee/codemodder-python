import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_break_or_continue_out_of_loop import (
    SonarBreakOrContinueOutOfLoop,
)


class TestSonarSQLParameterization(BaseSASTCodemodTest):
    codemod = SonarBreakOrContinueOutOfLoop
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "break-or-continue-out-of-loop-S1716"

    def test_simple(self, tmpdir):
        input_code = """
        def f():
            continue
        """
        expected = """
        def f():
            pass
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S1716",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 4,
                        "endOffset": 12,
                    },
                }
            ]
        }
        changes = self.run_and_assert(
            tmpdir, input_code, expected, results=json.dumps(issues)
        )
        assert changes is not None
        assert changes[0].changes[0].finding is not None
        # assert changes[0].changes[0].finding.id == "1"
        # assert (
        #     changes[0].changes[0].finding.rule.id
        #     == "python.django.security.audit.secure-cookies.django-secure-set-cookie"
        # )
