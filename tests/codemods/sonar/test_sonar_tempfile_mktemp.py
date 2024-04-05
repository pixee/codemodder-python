import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_tempfile_mktemp import SonarTempfileMktemp


class TestSonarTempfileMktemp(BaseSASTCodemodTest):
    codemod = SonarTempfileMktemp
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "secure-tempfile-S5445"

    def test_simple(self, tmpdir):
        input_code = """
        import tempfile
        
        tempfile.mktemp()
        """
        expected = """
        import tempfile
        
        tempfile.mkstemp()
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5445",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 4,
                        "endLine": 4,
                        "startOffset": 0,
                        "endOffset": 17,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
