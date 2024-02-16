import json
from core_codemods.sonar.sonar_literal_or_new_object_identity import (
    SonarLiteralOrNewObjectIdentity,
)
from tests.codemods.base_codemod_test import BaseSASTCodemodTest


class TestSonarLiteralOrNewObjectIdentity(BaseSASTCodemodTest):
    codemod = SonarLiteralOrNewObjectIdentity
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "literal-or-new-object-identity-S5796"

    def test_list(self, tmpdir):
        input_code = """
        l is [1,2,3]
        """
        expected = """
        l == [1,2,3]
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5796",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 2,
                        "endOffset": 4,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
