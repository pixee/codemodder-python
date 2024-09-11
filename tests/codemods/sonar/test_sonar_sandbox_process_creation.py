import json

import mock

from codemodder.codemods.test import BaseSASTCodemodTest
from codemodder.dependency import Security
from core_codemods.sonar.sonar_sandbox_process_creation import (
    SonarSandboxProcessCreation,
)


class TestSonarSandboxProcessCreation(BaseSASTCodemodTest):
    codemod = SonarSandboxProcessCreation
    tool = "sonar"

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
        issues = {
            "issues": [
                {
                    "rule": "pythonsecurity:S2076",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 9,
                        "endLine": 9,
                        "startOffset": 17,
                        "endOffset": 34,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
        adds_dependency.assert_called_once_with(Security)
