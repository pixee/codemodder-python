import libcst as cst
from codemodder.dependency_manager import DependencyManager
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class ProcessSandbox(SemgrepCodemod):
    NAME = "process-sandbox"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = (
        "Replaces subprocess.{func} with more secure safe_command library functions."
    )

    @classmethod
    def rule(cls):
        return """
        rules:
          - id: sandbox-process-creation
            pattern-either:
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
        """

    def on_result_found(self, original_node, updated_node):
        self.add_needed_import("security", "safe_command")
        DependencyManager().add(["security==1.0.1"])
        return self.update_call_target(
            updated_node,
            "safe_command",
            replacement_args=[cst.Arg(original_node.func), *original_node.args],
        )
