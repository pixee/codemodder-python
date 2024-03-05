from codemodder.codemods.libcst_transformer import NewArg
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class LxmlSafeParsing(SimpleCodemod):
    metadata = Metadata(
        name="safe-lxml-parsing",
        summary="Use Safe Parsers in `lxml` Parsing Functions",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://lxml.de/apidoc/lxml.etree.html#lxml.etree.XMLParser"
            ),
            Reference(
                url="https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing"
            ),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html"
            ),
        ],
    )
    change_description = (
        "Call `lxml.etree.parse` and `lxml.etree.fromstring` with a safe parser."
    )
    detector_pattern = """
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
