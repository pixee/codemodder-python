from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class LxmlSafeParserDefaults(SemgrepCodemod):
    NAME = "safe-lxml-parser-defaults"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    SUMMARY = "Enable all security checks in `lxml.etree.XMLParser` call."
    DESCRIPTION = "...........TODO"

    @classmethod
    def rule(cls):
        return """
            rules:
                - patterns:
                  - pattern: lxml.etree.$CLASS(...)
                  - pattern-not: lxml.etree.$CLASS(..., resolve_entities=False, ...)
                  - pattern-not: lxml.etree.$CLASS(..., no_network=True, ..., resolve_entities=False, ...)
                  - pattern-not: lxml.etree.$CLASS(..., dtd_validation=False, ..., resolve_entities=False, ...)
                  - metavariable-pattern:
                      metavariable: $CLASS
                      patterns:
                        - pattern-either:
                          - pattern: XMLParser
                          - pattern: ETCompatXMLParser
                          - pattern: XMLTreeBuilder
                          - pattern: XMLPullParser
                  - pattern-inside: |
                      import lxml
                      ...
        """

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node,
            [
                NewArg(name="resolve_entities", value="False", add_if_missing=True),
                NewArg(name="no_network", value="True", add_if_missing=False),
                NewArg(name="dtd_validation", value="False", add_if_missing=False),
            ],
        )
        return self.update_arg_target(updated_node, new_args)
