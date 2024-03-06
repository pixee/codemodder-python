from abc import ABCMeta, abstractmethod
from typing import Mapping

import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor

from codemodder.codemods.api import SimpleCodemod
from codemodder.codemods.imported_call_modifier import ImportedCallModifier
from codemodder.dependency import Dependency


class MappingImportedCallModifier(ImportedCallModifier[Mapping[str, str]]):
    def update_attribute(self, true_name, original_node, updated_node, new_args):
        if not self.node_is_selected(original_node):
            return updated_node

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
        if not self.node_is_selected(original_node):
            return updated_node

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


class ImportModifierCodemod(SimpleCodemod, metaclass=ABCMeta):
    @property
    def dependency(self) -> Dependency | None:
        return None

    @property
    @abstractmethod
    def mapping(self) -> Mapping[str, str]:
        pass

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        if not self.node_is_selected(tree):
            return tree

        visitor = MappingImportedCallModifier(
            self.context,
            self.file_context,
            self.mapping,
            self.change_description,
            self.results,
        )
        result_tree = visitor.transform_module(tree)
        self.file_context.codemod_changes.extend(visitor.changes_in_file)
        if visitor.changes_in_file and (dependency := self.dependency):
            self.add_dependency(dependency)

        return result_tree
