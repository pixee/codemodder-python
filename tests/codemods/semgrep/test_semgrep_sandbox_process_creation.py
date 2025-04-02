import mock

from codemodder.codemods.test import BaseSASTCodemodTest
from codemodder.dependency import Security
from core_codemods.semgrep.semgrep_sandbox_process_creation import (
    SemgrepSandboxProcessCreation,
)


class TestSonarSandboxProcessCreation(BaseSASTCodemodTest):
    codemod = SemgrepSandboxProcessCreation
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "sandbox-process-creation"

    @mock.patch("codemodder.codemods.api.FileContext.add_dependency")
    def test_simple(self, adds_dependency, tmpdir):
        input_code = """
        import os
        from flask import render_template, request

        @app.route('/vuln', methods=['GET', 'POST'])
        def vuln():
            output = ""
            if request.method == 'POST':
                command = request.form.get('command')
                output = os.popen(command).read()
            return render_template('vuln.html', output=output)
        """.lstrip(
            "\n"
        )
        expected = """
        import os
        from flask import render_template, request
        from security import safe_command

        @app.route('/vuln', methods=['GET', 'POST'])
        def vuln():
            output = ""
            if request.method == 'POST':
                command = request.form.get('command')
                output = safe_command.run(os.popen, command).read()
            return render_template('vuln.html', output=output)
        """.lstrip(
            "\n"
        )
        self.run_and_assert(tmpdir, input_code, expected, results=SARIF)
        adds_dependency.assert_called_once_with(Security)


SARIF = """
{
  "runs": [
    {
      "tool": {"driver": {"name": "Semgrep OSS"}},
      "automationDetails": {
        "id": ".github/workflows/semgrep.yml:semgrep_scan/"
      },
      "conversion": {
        "tool": {
          "driver": {
            "name": "GitHub Code Scanning"
          }
        }
      },
      "results": [
        {
          "correlationGuid": "a90240a2-8d09-47eb-a1c5-0af9d5b225c9",
          "level": "error",
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "index": 1,
                  "uri": "code.py"
                },
                "region": {
                  "endColumn": 35,
                  "endLine": 9,
                  "startColumn": 18,
                  "startLine": 9
                }
              }
            }
          ],
          "message": {
            "text": "Found user-controlled data used in a system call. This could allow a malicious actor to execute commands. Use the 'subprocess' module instead, which is easier to use without accidentally exposing a command injection vulnerability."
          },
          "partialFingerprints": {
            "primaryLocationLineHash": "b897622e8906ac69:1"
          },
          "properties": {
            "github/alertNumber": 2,
            "github/alertUrl": "https://api.github.com/repos/nahsra/vulnerable-app-sample/code-scanning/alerts/2"
          },
          "rule": {
            "id": "python.lang.security.dangerous-system-call.dangerous-system-call",
            "index": 723
          },
          "ruleId": "python.lang.security.dangerous-system-call.dangerous-system-call"
        }
      ]
    }
  ]
}
"""
