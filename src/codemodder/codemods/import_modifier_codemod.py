from abc import ABCMeta, abstractmethod
from typing import Callable, Mapping

import libcst as cst
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor

from codemodder.codemods.api import LibcstResultTransformer
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


class ImportModifierCodemod(LibcstResultTransformer, metaclass=ABCMeta):
    result_filter: Callable[[cst.CSTNode], bool] | None = None

    @property
    def dependency(self) -> Dependency | None:
        return None

    @property
    @abstractmethod
    def mapping(self) -> Mapping[str, str]:
        pass

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = MappingImportedCallModifier(
            self.context,
            self.file_context,
            self.mapping,
            self.change_description,
            self.results,
            self.result_filter,
        )
        result_tree = visitor.transform_module(tree)
        self.file_context.codemod_changes.extend(visitor.changes_in_file)
        if visitor.changes_in_file and (dependency := self.dependency):
            self.add_dependency(dependency)

        return result_tree
