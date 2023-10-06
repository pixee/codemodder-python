from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class LxmlSafeParsing(SemgrepCodemod):
    NAME = "safe-lxml-parsing"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Use safe parsers in lxml parsing functions"
    DESCRIPTION = (
        "Call `lxml.etree.parse` and `lxml.etree.fromstring` with a safe parser"
    )

    @classmethod
    def rule(cls):
        return """
            rules:
                - pattern-either:
                  - patterns:
                    - pattern: lxml.etree.$FUNC(...)
                    - pattern-not: lxml.etree.$FUNC(...,parser=..., ...)
                    - metavariable-pattern:
                        metavariable: $FUNC
                        patterns:
                          - pattern-either:
                            - pattern: parse
                            - pattern: fromstring
                    - pattern-inside: |
                        import lxml
                        ...
                  - patterns:
                    - pattern: lxml.etree.$FUNC(..., parser=None, ...)
                    - metavariable-pattern:
                        metavariable: $FUNC
                        patterns:
                          - pattern-either:
                            - pattern: parse
                            - pattern: fromstring
                    - pattern-inside: |
                        import lxml
                        ...
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("lxml")
        safe_parser = "lxml.etree.XMLParser(resolve_entities=False)"
        new_args = self.replace_args(
            original_node,
            [NewArg(name="parser", value=safe_parser, add_if_missing=True)],
        )
        return self.update_arg_target(updated_node, new_args)
