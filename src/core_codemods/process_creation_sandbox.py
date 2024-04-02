import libcst as cst

from codemodder.dependency import Security
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class ProcessSandbox(SimpleCodemod):
    metadata = Metadata(
        name="sandbox-process-creation",
        summary="Sandbox Process Creation",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://github.com/pixee/python-security/blob/main/src/security/safe_command/api.py"
            ),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
            ),
        ],
    )
    change_description = (
        "Replaces subprocess.{func} with more secure safe_command library functions."
    )

    adds_dependency = True
    detector_pattern = """
        rules:
            - pattern-either:
              - patterns:
                - pattern: subprocess.$FUNC(...)
                - pattern-not: subprocess.$FUNC("...", ...)
                - pattern-not: subprocess.$FUNC(["...", ...], ...)
                - metavariable-pattern:
                    metavariable: $FUNC
                    patterns:
                    - pattern-either:
                      - pattern: run
                      - pattern: call
                      - pattern: Popen
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
