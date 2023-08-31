from typing import List, Union
from isort.settings import Config

import libcst as cst
from libcst.codemod.visitors import GatherUnusedImportsVisitor
from libcst import (
    CSTTransformer,
    CSTVisitor,
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
        top_imports_visitor = GatherTopLevelImportBlocks()
        tree.visit(top_imports_visitor)
        # Do not change anything if not top level imports are found
        if top_imports_visitor.top_imports_blocks:
            return tree.visit(
                OrderImportsBlocksTransform(
                    self.src_path, top_imports_visitor.top_imports_blocks
                )
            )
        return tree


class ReplaceNodes(cst.CSTTransformer):
    """
    Replace nodes with their corresponding values in a given dict.
    """

    def __init__(
        self,
        replacements: dict[
            cst.CSTNode, Union[cst.CSTNode, cst.FlattenSentinel, cst.RemovalSentinel]
        ],
    ):
        self.replacements = replacements

    def on_leave(self, original_node, updated_node):
        if original_node in self.replacements.keys():
            return self.replacements[original_node]
        return updated_node


class OrderImportsBlocksTransform(CSTTransformer):
    """
    Given a list of import blocks, triage them in sections (__future__, standard, first party, third party and local, in this order) and orders them by name at the start of the module.  Mimics isort's default behavior.
    """

    def __init__(self, src_path, import_blocks):
        self.import_blocks: List[List[cst.SimpleStatementLine]] = import_blocks
        self.src_path = src_path

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        result_tree = original_node
        replacement_nodes: dict[
            cst.CSTNode, Union[cst.CSTNode, cst.FlattenSentinel, cst.RemovalSentinel]
        ] = {}
        for block in self.import_blocks:
            anchor = block[0]
            ordered_block = list(self._order_block(block))
            sentinel = cst.FlattenSentinel(ordered_block)
            replacement_nodes = replacement_nodes | {anchor: sentinel}
            # result_tree = result_tree.deep_replace(anchor, sentinel)
        ## remove all the imports except the first of each block
        for node in [node for lista in self.import_blocks for node in lista[1:]]:
            replacement_nodes = replacement_nodes | {node: RemovalSentinel.REMOVE}
        result_tree = result_tree.visit(ReplaceNodes(replacement_nodes))
        return result_tree

    def _trim_leading_lines(self, stmt: cst.SimpleStatementLine) -> List[cst.EmptyLine]:
        """
        For a given SimpleStatementLine, gather the list of comments right above it.
        """
        lista: List[cst.EmptyLine] = []
        for empty_line in reversed(stmt.leading_lines):
            if matchers.matches(
                empty_line, matchers.EmptyLine(comment=matchers.Comment())
            ):
                lista.append(empty_line)
            else:
                lista.reverse()
                return lista
        lista.reverse()
        return lista

    def _handle_regular_imports(self, import_stmts):
        # bin them into (name,alias) for deduplication and comment merging
        # the value of the dict contains the comment blocks from all the same imports
        alias_dict = defaultdict(list)
        for stmt in import_stmts:
            imp = stmt.body[0]
            comments = self._trim_leading_lines(stmt)
            # only the first import in a list will inherit the comments
            first_ia = imp.names[0]
            alias_dict[(first_ia.evaluated_name, first_ia.evaluated_alias)].append(
                comments
            )
            for ia in imp.names[1:]:
                alias_dict.setdefault((ia.evaluated_name, ia.evaluated_alias), [])

        # create the statements for each pair in alias_dict
        new_import_stmts = []
        for name, asname in alias_dict.keys():
            ia = cst.ImportAlias(
                name=cst.Name(name),
                asname=(asname and cst.AsName(cst.Name(asname))),
            )
            # invert the comment blocks and flatten
            comments = list(
                itertools.chain.from_iterable(reversed(alias_dict[(name, asname)]))
            )
            new_import_stmts.append(
                cst.SimpleStatementLine(
                    body=[cst.Import(names=[ia])], leading_lines=comments
                )
            )
        return new_import_stmts

    def _handle_from_imports(self, from_import_stmts):
        imports_dict = defaultdict(lambda: (set, []))
        # binsort the aliases into module name, merge comments
        for stmt in from_import_stmts:
            imp = stmt.body[0]
            comments = self._trim_leading_lines(stmt)
            all_ia_from_imp = {
                (ia.evaluated_name, ia.evaluated_alias) for ia in imp.names
            }
            imports_dict[_get_name(imp)][0].update(all_ia_from_imp)
            imports_dict[_get_name(imp)][1].append(comments)

        # creates the stmt for each dictionary entry
        new_from_import_stmts = []
        for module_name, tupla in imports_dict.items():
            split = re.split(r"^(\.+)", module_name)
            actual_name = split[-1]

            n_dots = 0 if len(split) == 1 else len(split[1])
            all_ia = [
                cst.ImportAlias(
                    name=cst.Name(name),
                    asname=(asname and cst.AsName(cst.Name(asname))),
                )
                for name, asname in tupla[1]
            ]
            comments = list(itertools.chain.from_iterable(reversed(tupla[1])))
            new_from_import_stmts.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=_node_from_name(actual_name),
                            names=all_ia,
                            relative=[cst.Dot()] * n_dots,
                        )
                    ],
                    leading_lines=comments,
                )
            )
        return new_from_import_stmts

    def _order_block(self, imports_block):
        # triage from imports from regular imports
        from_imports = []
        regular_imports = []
        for stmt in imports_block:
            imp = stmt.body[0]
            if matchers.matches(imp, matchers.ImportFrom()):
                from_imports.append(stmt)
            if matchers.matches(imp, matchers.Import()):
                regular_imports.append(stmt)

        # create the new statements to be inserted accoding to cases
        regular_import_stmts = self._handle_regular_imports(regular_imports)
        from_import_stmts = self._handle_from_imports(from_imports)

        # classify by sections and sort each section by module name
        imports_by_section = _triage_imports(
            itertools.chain(regular_import_stmts, from_import_stmts),
            self.src_path,
        )
        _sort_each_section(imports_by_section)

        # add empty lines after each section
        for section in imports_by_section[:-1]:
            if section:
                section.append(cst.EmptyLine())
        # return flat list of statement nodes

        return itertools.chain.from_iterable(imports_by_section)


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
        section.sort(key=lambda stmt: _natural_key(_get_name(stmt.body[0])))


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

    for stmt in all_imports:
        imp = stmt.body[0]
        section = isort.place.module(_get_name(imp), config)

        if section == isort.sections.FUTURE:
            future.append(stmt)
        elif section == isort.sections.STDLIB:
            stdlib.append(stmt)
        elif section == isort.sections.LOCALFOLDER:
            local.append(stmt)
        elif section == isort.sections.FIRSTPARTY:
            first_party.append(stmt)
        else:
            third_party.append(stmt)

    # filter empty sections
    return list(filter(lambda x: x, [future, stdlib, third_party, first_party, local]))


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
