import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_tempfile_mktemp import SonarTempfileMktemp


class TestSonarTempfileMktemp(BaseSASTCodemodTest):
    codemod = SonarTempfileMktemp
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "secure-tempfile"

    def test_simple(self, tmpdir):
        input_code = """
        import tempfile
        
        filename = tempfile.mktemp()
        """
        expected = """
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            filename = tf.name
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
        unfixed = self.execution_context.get_unfixed_findings(self.codemod.id)
        assert len(unfixed) == 0

    def test_unfixed(self, tmpdir):
        RULE_ID = "python:S5445"

        input_code = (
            expected
        ) = """
        import tempfile

        tmp_file = open(tempfile.mktemp(), "w+")
        tmp_file.write("text")
        """

        issues = {
            "issues": [
                {
                    "rule": RULE_ID,
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 4,
                        "endLine": 4,
                        "startOffset": 15,
                        "endOffset": 33,
                    },
                }
            ]
        }

        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))

        unfixed = self.execution_context.get_unfixed_findings(self.codemod.id)
        assert len(unfixed) == 1
        assert unfixed[0].id == RULE_ID
        assert unfixed[0].rule.id == RULE_ID
        assert unfixed[0].lineNumber == 4
        assert unfixed[0].reason == "Pixee does not yet support this fix."
        assert unfixed[0].path == "code.py"
