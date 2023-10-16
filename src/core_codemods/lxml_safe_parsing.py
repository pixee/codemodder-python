from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.api.helpers import NewArg


class LxmlSafeParsing(SemgrepCodemod):
    NAME = "safe-lxml-parsing"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Use Safe Parsers in `lxml` Parsing Functions"
    DESCRIPTION = (
        "Call `lxml.etree.parse` and `lxml.etree.fromstring` with a safe parser."
    )
    REFERENCES = [
        {
            "url": "https://lxml.de/apidoc/lxml.etree.html#lxml.etree.XMLParser",
            "description": "",
        },
        {
            "url": "https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing",
            "description": "",
        },
        {
            "url": "https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html",
            "description": "",
        },
    ]

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
                        import lxml.etree
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
                        import lxml.etree
                        ...
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("lxml.etree")
        safe_parser = "lxml.etree.XMLParser(resolve_entities=False)"
        new_args = self.replace_args(
            original_node,
            [NewArg(name="parser", value=safe_parser, add_if_missing=True)],
        )
        return self.update_arg_target(updated_node, new_args)
