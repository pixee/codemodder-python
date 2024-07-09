import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_subprocess_shell_false import (
    SemgrepSubprocessShellFalse,
)


class TestSemgrepSubprocessShellFalse(BaseSASTCodemodTest):
    codemod = SemgrepSubprocessShellFalse
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "subprocess-shell-false"

    def test_import(self, tmpdir):
        input_code = """\
        from subprocess import run
        run(args, shell=True)
        """
        expexted_output = """\
        from subprocess import run
        run(args, shell=False)
        """

        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 22,
                                            "endLine": 2,
                                            "snippet": {
                                                "text": "run(args, shell=True)"
                                            },
                                            "startColumn": 1,
                                            "startLine": 2,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Found 'subprocess' function 'run' with 'shell=True'. This is dangerous because this call will spawn the command using a shell process. Doing so propagates current shell settings and variables, which makes it much easier for a malicious actor to execute commands. Use 'shell=False' instead."
                            },
                            "properties": {},
                            "ruleId": "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true",
                        }
                    ]
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expexted_output,
            results=json.dumps(results),
        )
