from functools import cached_property
from typing import Mapping

import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from core_codemods.api import (
    SimpleCodemod,
    Metadata,
    Reference,
    ReviewGuidance,
)
from codemodder.codemods.imported_call_modifier import ImportedCallModifier
from codemodder.dependency import DefusedXML


class DefusedXmlModifier(ImportedCallModifier[Mapping[str, str]]):
    def update_attribute(self, true_name, original_node, updated_node, new_args):
        import_name = self.matching_functions[true_name]
        AddImportsVisitor.add_needed_import(self.context, import_name)
        RemoveImportsVisitor.remove_unused_import_by_node(self.context, original_node)
        return updated_node.with_changes(
            args=new_args,
            func=cst.Attribute(
                value=cst.parse_expression(import_name),
                attr=cst.Name(value=true_name.split(".")[-1]),
            ),
        )

    def update_simple_name(self, true_name, original_node, updated_node, new_args):
        import_name = self.matching_functions[true_name]
        AddImportsVisitor.add_needed_import(self.context, import_name)
        RemoveImportsVisitor.remove_unused_import_by_node(self.context, original_node)
        return updated_node.with_changes(
            args=new_args,
            func=cst.Attribute(
                value=cst.parse_expression(import_name),
                attr=cst.Name(value=true_name.split(".")[-1]),
            ),
        )


ETREE_METHODS = ["parse", "fromstring", "iterparse", "XMLParser"]
SAX_METHODS = ["parse", "make_parser", "parseString"]
DOM_METHODS = ["parse", "parseString"]
# TODO: add expat methods?


class UseDefusedXml(SimpleCodemod):
    metadata = Metadata(
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
    )

    change_description = "Replace builtin XML method with safe `defusedxml` method"

    @cached_property
    def matching_functions(self) -> dict[str, str]:
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

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = DefusedXmlModifier(
            self.context,
            self.file_context,
            self.matching_functions,
            self.change_description,
        )
        result_tree = visitor.transform_module(tree)
        self.file_context.codemod_changes.extend(visitor.changes_in_file)
        if visitor.changes_in_file:
            self.add_dependency(DefusedXML)

        return result_tree
