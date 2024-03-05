from codemodder.codemods.libcst_transformer import NewArg
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class LxmlSafeParserDefaults(SimpleCodemod):
    metadata = Metadata(
        name="safe-lxml-parser-defaults",
        summary="Use Safe Defaults for `lxml` Parsers",
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
    change_description = "Replace `lxml` parser parameters with safe defaults."
    detector_pattern = """
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
                      import lxml.etree
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
