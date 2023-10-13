from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class TempfileMktemp(SemgrepCodemod):
    NAME = "secure-tempfile"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Upgrade and Secure Temp File Creation"
    DESCRIPTION = "Replaces `tempfile.mktemp` with `tempfile.mkstemp`."
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/library/tempfile.html#tempfile.mktemp",
            "description": "",
        }
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - patterns:
            - pattern: tempfile.mktemp(...)
            - pattern-inside: |
                import tempfile
                ...
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("tempfile")
        return self.update_call_target(updated_node, "tempfile", "mkstemp")
