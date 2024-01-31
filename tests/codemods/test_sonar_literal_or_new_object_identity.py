import json
from core_codemods.sonar.sonar_literal_or_new_object_identity import (
    SonarLiteralOrNewObjectIdentity,
)
from tests.codemods.base_codemod_test import BaseSASTCodemodTest
from textwrap import dedent


class TestSonarLiteralOrNewObjectIdentity(BaseSASTCodemodTest):
    codemod = SonarLiteralOrNewObjectIdentity
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "literal-or-new-object-identity-S5796"

    def test_list(self, tmpdir):
        input_code = """\
        l is [1,2,3]
        """
        expected = """\
        l == [1,2,3]
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5796",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 1,
                        "endLine": 1,
                        "startOffset": 2,
                        "endOffset": 4,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir, dedent(input_code), dedent(expected), results=json.dumps(issues)
        )
