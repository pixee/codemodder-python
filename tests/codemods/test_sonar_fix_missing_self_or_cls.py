import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_fix_missing_self_or_cls import SonarFixMissingSelfOrCls


class TestSonarFixMissingSelfOrCls(BaseSASTCodemodTest):
    codemod = SonarFixMissingSelfOrCls
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "fix-missing-self-or-cls-S5719"

    def test_simple(self, tmpdir):
        input_code = """
        class A:
            def method():
                pass
            
            @classmethod
            def clsmethod():
                pass
        """
        expected_output = """
        class A:
            def method(self):
                pass
            
            @classmethod
            def clsmethod(cls):
                pass
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5719",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 4,
                        "endOffset": 25,
                    },
                },
                {
                    "rule": "python:S5719",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 6,
                        "endLine": 6,
                        "startOffset": 4,
                        "endOffset": 22,
                    },
                },
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(issues),
            num_changes=2,
        )
