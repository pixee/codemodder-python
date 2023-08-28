from typing import List, Set, Union
from isort.settings import Config

import libcst as cst
from libcst.codemod.visitors import GatherUnusedImportsVisitor
from libcst import (
    CSTTransformer,
    CSTVisitor,
    FlattenSentinel,
    RemovalSentinel,
    matchers,
)
import re
from collections import defaultdict
from libcst.codemod import Codemod, CodemodContext, ContextAwareTransformer
from libcst.metadata import GlobalScope, ScopeProvider
import itertools
from libcst.helpers import get_full_name_for_node
import isort.place
import isort.sections


from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsCodemod,
)


class CleanImports(Codemod):
    """
    Cleans and organizes the imports of a module. It removes any unused imports and triages the global imports by sections (__future__, standard, first party, third party and local, in this order). Each section is then sorted by its module name and each from import is also sorted by name. Sorts are natural.
    """

    METADATA_DEPENDENCIES = (*GatherUnusedImportsVisitor.METADATA_DEPENDENCIES,)

    def __init__(self, context, src_path):
        """
        :param src_path: a Path for the project root
        """
        super().__init__(context)
        self.src_path = src_path

    def transform_module_impl(self, tree: cst.Module):
        # gather and remove unused imports
        result_tree = RemoveUnusedImportsCodemod(self.context).transform_module(tree)
        return OrderTopLevelImports(self.context, self.src_path).transform_module(
            result_tree
        )


class OrderTopLevelImports(Codemod):
    """
    Triage the top level imports in sections (__future__, standard, first party, third party and local, in this order) and orders them by name at the start of the module.  Mimics isort's default behavior.
    """

    def __init__(self, context: CodemodContext, src_path):
        super().__init__(context)
        self.src_path = src_path

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        top_imports_visitor = GatherTopLevelImports()
        tree.visit(top_imports_visitor)
        # Do not change anything if not top level imports are found
        if top_imports_visitor.top_imports:
            return tree.visit(
                OrderImportsTransform(self.src_path, top_imports_visitor.top_imports)
            )
        return tree


class OrderImportsTransform(CSTTransformer):
    """
    Given a list of imports, triage them in sections (__future__, standard, first party, third party and local, in this order) and orders them by name at the start of the module.  Mimics isort's default behavior.
    """

    def __init__(self, src_path, imports_to_order):
        self.imports_to_order = imports_to_order
        self.src_path = src_path

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        # remove the nodes from the tree
        result_tree = original_node.visit(RemoveNodes(self.imports_to_order))

        # binsort the import alias by module, normal imports are binned into ''
        # aliases are represented by (ia.evaluated_name, ia.evaluated_alias) for deduplication
        imports_dict = defaultdict(set)
        for imp in self.imports_to_order:
            if matchers.matches(imp, matchers.ImportFrom()):
                all_ia_from_imp = {
                    (ia.evaluated_name, ia.evaluated_alias) for ia in imp.names
                }
                imports_dict[_get_name(imp)].update(all_ia_from_imp)
            if matchers.matches(imp, matchers.Import()):
                for ia in imp.names:
                    imports_dict[""].add((ia.evaluated_name, ia.evaluated_alias))

        # create the aliases for each bin
        imports_alias_dict = {
            k: [
                cst.ImportAlias(
                    name=cst.Name(name),
                    asname=(asname and cst.AsName(cst.Name(asname))),
                )
                for name, asname in v
            ]
            for k, v in imports_dict.items()
        }

        # create the direct module imports
        module_imports_set = [
            cst.Import(names=[ia]) for ia in imports_alias_dict.pop("", set())
        ]

        # create the from imports and sort them
        from_imports_set = set()
        for k, v in imports_alias_dict.items():
            # remove relative dots from the start of the name
            split = re.split(r"^(\.+)", k)
            actual_name = split[-1]
            n_dots = 0 if len(split) == 1 else len(split[1])
            from_imports_set.add(
                cst.ImportFrom(
                    module=_node_from_name(actual_name),
                    names=sorted(
                        v,
                        key=lambda import_alias: _natural_key(
                            import_alias.evaluated_name
                        ),
                    ),
                    relative=[cst.Dot()] * n_dots,
                )
            )

        # classify by sections and sort each section by module name
        imports_by_section = _triage_imports(
            itertools.chain(module_imports_set, from_imports_set),
            self.src_path,
        )
        _sort_each_section(imports_by_section)

        # wrap all the imports into statements, remove empty sections
        all_import_statement = [
            [cst.SimpleStatementLine(body=[imp]) for imp in section]
            for section in imports_by_section
            if section
        ]

        # add empty lines after each section
        for section in all_import_statement[:-1]:
            if section:
                section.append(cst.EmptyLine())

        # rewrite all the imports, tree may be empty
        if result_tree.children:
            # Find first child that is not a comment or docstring
            first_statement = result_tree.children[0]
            all_import_statement.append(
                [
                    cst.EmptyLine(),
                    first_statement.with_changes(leading_lines=[]),
                ]
            )
            sentinel = cst.FlattenSentinel(
                itertools.chain.from_iterable(all_import_statement)
            )
            result_tree = result_tree.deep_replace(first_statement, sentinel)
            return result_tree
        return result_tree.with_changes(
            body=list(itertools.chain.from_iterable(all_import_statement))
        )


class RemoveNodes(CSTTransformer):
    """
    Remove given nodes from the tree.
    """

    def __init__(self, nodes_to_remove: Set[cst.CSTNode]):
        self.nodes_to_remove = nodes_to_remove

    def on_leave(
        self, original_node: cst.CSTNodeT, updated_node: cst.CSTNodeT
    ) -> Union[cst.CSTNodeT, RemovalSentinel, FlattenSentinel[cst.CSTNodeT]]:
        if original_node in self.nodes_to_remove:
            return RemovalSentinel.REMOVE
        return updated_node


class GatherTopLevelImportBlocks(CSTVisitor):
    """
    Gather all the import blocks at the "top level" of global scope.
    """

    def __init__(self) -> None:
        self.top_imports_blocks: List[List[cst.SimpleStatementLine]] = []

    def leave_Module(self, original_node: cst.Module):
        blocks = []
        current_block: List[cst.SimpleStatementLine] | None = None
        for stmt in original_node.body:
            if matchers.matches(
                stmt,
                matchers.SimpleStatementLine(
                    body=[matchers.ImportFrom() | matchers.Import()]
                ),
            ):
                if current_block:
                    current_block.append(stmt)
                else:
                    current_block = [stmt]
            else:
                if current_block:
                    blocks.append(current_block)
                current_block = None

        if current_block:
            blocks.append(current_block)
        self.top_imports_blocks = blocks


class GatherTopLevelImports(CSTVisitor):
    """
    Gather all the imports from the global scope at the "top level".
    """

    def __init__(self) -> None:
        self.top_imports: Set[cst.Import | cst.ImportFrom] = set()

    def leave_Module(self, original_node: cst.Module):
        for stmt in original_node.body:
            if matchers.matches(
                stmt,
                matchers.SimpleStatementLine(
                    body=[matchers.ImportFrom() | matchers.Import()]
                ),
            ):
                self.top_imports.add(stmt.body[0])


class GatherAndRemoveImportsTransformer(ContextAwareTransformer, cst.MetadataDependent):
    """
    Removes all the imports in the global scope of a module and gather them in global_imports.
    """

    METADATA_DEPENDENCIES = (ScopeProvider,)

    def __init__(self, context) -> None:
        super().__init__(context)
        self.global_imports: List[cst.CSTNode] = []

    def leave_Import(self, original_node, updated_node):
        scope = self.get_metadata(ScopeProvider, original_node)
        if isinstance(scope, GlobalScope):
            self.global_imports.append(original_node)
            return cst.RemoveFromParent()
        return original_node

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.Import):
        scope = self.get_metadata(ScopeProvider, original_node)
        if isinstance(scope, GlobalScope):
            self.global_imports.append(original_node)
            return cst.RemoveFromParent()
        return original_node


def _sort_each_section(imports_by_section):
    """
    Given a list of lists containing imports by sections, natural sort each section in-place by its module name.
    """
    for section in imports_by_section:
        section.sort(key=lambda imp: _natural_key(_get_name(imp)))


def _triage_imports(all_imports, src_path):
    """
    Triage a list of imports into sections: future, stdlib, first party, third party and local.
    """
    future = []
    stdlib = []
    first_party: List[cst.CSTNode] = []
    third_party = []
    local = []

    config = Config(src_paths=(src_path,))

    for imp in all_imports:
        section = isort.place.module(_get_name(imp), config)

        if section == isort.sections.FUTURE:
            future.append(imp)
        elif section == isort.sections.STDLIB:
            stdlib.append(imp)
        elif section == isort.sections.LOCALFOLDER:
            local.append(imp)
        elif section == isort.sections.FIRSTPARTY:
            first_party.append(imp)
        else:
            third_party.append(imp)

    imports_by_section = [future, stdlib, third_party, first_party, local]
    return imports_by_section


def _natural_key(s):
    """
    Converts a string into a key for natural sorting.
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    return [convert(imp) for imp in re.split(r"([0-9]+)", s)]


def _node_from_name_parts(parts):
    if len(parts) == 1:
        return cst.Name(parts[0])
    h, *tail = parts
    return cst.Attribute(attr=cst.Name(h), value=_node_from_name_parts(tail))


def _node_from_name(name):
    """
    Creates a node representing a name.
    Either a simple Name or an attribute if sectioned by dots.
    """
    parts = name.split(".")
    parts.reverse()
    return _node_from_name_parts(parts)


def _get_name(node):
    """
    Get the full name of a module referenced by a Import or ImportFrom node.
    For relative modules, dots are added at the beginning
    """
    if matchers.matches(node, matchers.ImportFrom()):
        return "." * len(node.relative) + get_full_name_for_node(node.module)
    if matchers.matches(node, matchers.Import()):
        return get_full_name_for_node(node.names[0].name)
    return ""
