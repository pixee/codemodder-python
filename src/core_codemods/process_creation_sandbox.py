import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.dependency import Security


class ProcessSandbox(SemgrepCodemod):
    NAME = "sandbox-process-creation"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Sandbox Process Creation"
    DESCRIPTION = (
        "Replaces subprocess.{func} with more secure safe_command library functions."
    )
    REFERENCES = [
        {
            "url": "https://github.com/pixee/python-security/blob/main/src/security/safe_command/api.py",
            "description": "",
        },
        {
            "url": "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html",
            "description": "",
        },
    ]

    adds_dependency = True

    @classmethod
    def rule(cls):
        return """
        rules:
            - pattern-either:
              - patterns:
                - pattern: subprocess.run(...)
                - pattern-inside: |
                    import subprocess
                    ...
              - patterns:
                - pattern: subprocess.call(...)
                - pattern-inside: |
                    import subprocess
                    ...
              - patterns:
                - pattern: subprocess.Popen(...)
                - pattern-inside: |
                    import subprocess
                    ...
        """

    def on_result_found(self, original_node, updated_node):
        self.add_needed_import("security", "safe_command")
        self.add_dependency(Security)
        return self.update_call_target(
            updated_node,
            "safe_command",
            new_func="run",
            replacement_args=[cst.Arg(original_node.func), *original_node.args],
        )
