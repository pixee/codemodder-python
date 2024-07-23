from functools import cached_property

from codemodder.codemods.import_modifier_codemod import ImportModifierCodemod
from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from codemodder.dependency import DefusedXML, Dependency
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance

ETREE_METHODS = ["parse", "fromstring", "iterparse", "XMLParser"]
SAX_METHODS = ["parse", "make_parser", "parseString"]
DOM_METHODS = ["parse", "parseString"]
# TODO: add expat methods?


class UseDefusedXmlTransformer(ImportModifierCodemod):
    change_description = "Replace builtin XML method with safe `defusedxml` method"

    @cached_property
    def mapping(self) -> dict[str, str]:
        """Build a mapping of functions to their defusedxml imports"""
        _matching_functions: dict[str, str] = {}
        for module, defusedxml, methods in [
            ("xml.etree.ElementTree", "defusedxml.ElementTree", ETREE_METHODS),
            ("xml.etree.cElementTree", "defusedxml.ElementTree", ETREE_METHODS),
            ("xml.sax", "defusedxml.sax", SAX_METHODS),
            ("xml.dom.minidom", "defusedxml.minidom", DOM_METHODS),
            ("xml.dom.pulldom", "defusedxml.pulldom", DOM_METHODS),
        ]:
            _matching_functions.update(
                {f"{module}.{method}": defusedxml for method in methods}
            )
        return _matching_functions

    @property
    def dependency(self) -> Dependency:
        return DefusedXML


UseDefusedXml = CoreCodemod(
    metadata=Metadata(
        name="use-defusedxml",
        summary="Use `defusedxml` for Parsing XML",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/xml.html#xml-vulnerabilities"
            ),
            Reference(
                url="https://docs.python.org/3/library/xml.html#the-defusedxml-package"
            ),
            Reference(url="https://pypi.org/project/defusedxml/"),
            Reference(
                url="https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(UseDefusedXmlTransformer),
)
