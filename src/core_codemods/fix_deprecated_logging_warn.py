import libcst as cst
from codemodder.codemods.api import SemgrepCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class FixDeprecatedLoggingWarn(SemgrepCodemod, NameResolutionMixin):
    NAME = "fix-deprecated-logging-warn"
    SUMMARY = "Replace Deprecated `logging.warn`"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Replace deprecated `logging.warn` with `logging.warning`"
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/library/logging.html#logging.Logger.warning",
            "description": "",
        },
    ]
    _module_name = "logging"

    @classmethod
    def rule(cls):
        return """
        rules:
            - pattern-either:
              - patterns:
                - pattern: logging.warn(...)
                - pattern-inside: |
                    import logging
                    ...
              - patterns:
                - pattern: logging.getLogger(...).warn(...)
                - pattern-inside: |
                    import logging
                    ...
              - patterns:
                - pattern: $VAR.warn(...)
                - pattern-inside: |
                    import logging
                    ...
                    $VAR = logging.getLogger(...)
                    ...

        """

    def on_result_found(self, original_node, updated_node):
        warning = cst.Name(value="warning")
        match original_node.func:
            case cst.Name():
                self.add_needed_import(self._module_name, "warning")
                self.remove_unused_import(original_node.func)
                return updated_node.with_changes(func=warning)
            case cst.Attribute():
                return updated_node.with_changes(
                    func=updated_node.func.with_changes(attr=warning)
                )
        return original_node
