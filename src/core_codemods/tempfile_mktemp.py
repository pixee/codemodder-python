from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.utils_mixin import NameResolutionMixin


class TempfileMktemp(SemgrepCodemod, NameResolutionMixin):
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

    _module_name = "tempfile"

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
        maybe_name = self.get_aliased_prefix_name(original_node, self._module_name)
        maybe_name = maybe_name or self._module_name
        if maybe_name == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)
        return self.update_call_target(updated_node, maybe_name, "mkstemp")
