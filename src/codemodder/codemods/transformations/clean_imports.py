import itertools
import re
from collections import defaultdict
from typing import List, Union

import isort.place
import isort.sections
import libcst as cst
from isort.settings import Config
from libcst import CSTTransformer, CSTVisitor, MaybeSentinel, RemovalSentinel, matchers
from libcst.codemod import Codemod, CodemodContext, ContextAwareTransformer
from libcst.codemod.visitors import GatherUnusedImportsVisitor
from libcst.helpers import get_full_name_for_node
from libcst.metadata import GlobalScope, ScopeProvider

from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsCodemod,
)
from codemodder.codemods.utils import ReplaceNodes


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
        # Do not change anything if no top level imports are found
        if top_imports_visitor.top_imports_blocks:
            return tree.visit(
                OrderImportsBlocksTransform(
                    self.src_path, top_imports_visitor.top_imports_blocks
                )
            )
        return tree


class OrderImportsBlocksTransform(CSTTransformer):
    """
    Given a list of import blocks, triage them in sections (__future__, standard, first party, third party and local, in this order) and orders them by name at the start of the module.  Mimics isort's default behavior.
    """

    def __init__(self, src_path, import_blocks):
        self.import_blocks: List[List[cst.SimpleStatementLine]] = import_blocks
        self.src_path = src_path
        self.changes = [False] * len(import_blocks)

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        result_tree = original_node
        replacement_nodes: dict[
            cst.CSTNode,
            Union[cst.CSTNode, cst.FlattenSentinel[cst.CSTNode], cst.RemovalSentinel],
        ] = {}
        for i, block in enumerate(self.import_blocks):
            anchor = block[0]
            ordered_block = list(self._order_block(block))

            # gather all the leading lines from anchor until the comments
            new_anchor_head = list(anchor.leading_lines[: _split_leading_lines(anchor)])
            new_anchor_head.extend(ordered_block[0].leading_lines)
            ordered_block[0] = ordered_block[0].with_changes(
                leading_lines=new_anchor_head
            )

            # check if anything changed
            self.changes[i] = not all(
                map(
                    lambda t: t[0].deep_equals(t[1]),
                    zip(self.import_blocks[i], ordered_block),
                )
            )
            sentinel = cst.FlattenSentinel(ordered_block)

            replacement_nodes = replacement_nodes | {anchor: sentinel}
            # result_tree = result_tree.deep_replace(anchor, sentinel)

        # remove all the imports except the first of each block
        for node in [node for lista in self.import_blocks for node in lista[1:]]:
            replacement_nodes = replacement_nodes | {node: RemovalSentinel.REMOVE}
        result_tree = result_tree.visit(ReplaceNodes(replacement_nodes))
        return result_tree

    def _create_import_statement(self, name, alias, comments):
        ia = cst.ImportAlias(
            name=_node_from_name(name),
            asname=(alias and cst.AsName(cst.Name(alias))),
        )
        return cst.SimpleStatementLine(
            body=[cst.Import(names=[ia])], leading_lines=comments
        )

    def _binsort_imports_by_name_alias(
        self, import_stmts
    ) -> defaultdict[tuple[str, str], list[cst.EmptyLine]]:
        alias_dict: defaultdict[tuple[str, str], list[cst.EmptyLine]] = defaultdict(
            list
        )
        for stmt in import_stmts:
            imp = stmt.body[0]
            comments = _trim_leading_lines(stmt)
            # only the first import in a list will inherit the comments
            first_ia = imp.names[0]
            alias_dict.setdefault(
                (first_ia.evaluated_name, first_ia.evaluated_alias), []
            )
            if comments:
                alias_dict[(first_ia.evaluated_name, first_ia.evaluated_alias)].append(
                    comments
                )
            for ia in imp.names[1:]:
                alias_dict.setdefault((ia.evaluated_name, ia.evaluated_alias), [])
        return alias_dict

    def _handle_regular_imports(self, import_stmts):
        # bin them into (name,alias) for deduplication and comment merging
        # the value of the dict contains the comment blocks from all the same imports
        alias_dict = self._binsort_imports_by_name_alias(import_stmts)

        # create the statements for each pair in alias_dict
        new_import_stmts = []
        for (name, alias), comments in alias_dict.items():
            # invert the comment blocks and flatten
            ordered_comments = list(itertools.chain.from_iterable(reversed(comments)))
            new_import_stmts.append(
                self._create_import_statement(name, alias, ordered_comments)
            )
        return new_import_stmts

    def _binsort_from_imports_by_module(self, from_import_stmts):
        imports_dict = defaultdict(lambda: (set(), []))
        star_imports_dict = defaultdict(list)
        # binsort the aliases into module names, merge comments
        for stmt in from_import_stmts:
            imp = stmt.body[0]
            comments = _trim_leading_lines(stmt)
            if matchers.matches(imp.names, matchers.ImportStar()):
                star_imports_dict[_get_name(imp)] = [comments]
            else:
                all_ia_from_imp = {
                    (ia.evaluated_name, ia.evaluated_alias) for ia in imp.names
                }
                imports_dict[_get_name(imp)][0].update(all_ia_from_imp)
                if comments:
                    imports_dict[_get_name(imp)][1].append(comments)
        return (imports_dict, star_imports_dict)

    def _create_from_import_stmt(self, module_name, name_alias_set, comments):
        sorted_name_alias = list(name_alias_set)
        sorted_name_alias.sort(key=lambda t: _natural_key(t[0]))
        all_ia = [
            cst.ImportAlias(
                name=cst.Name(name),
                asname=(asname and cst.AsName(cst.Name(asname))),
                comma=cst.Comma(
                    whitespace_before=cst.SimpleWhitespace(""),
                    whitespace_after=cst.SimpleWhitespace(" "),
                ),
            )
            for name, asname in sorted_name_alias
        ]
        # last one should not have a comma
        all_ia[-1] = all_ia[-1].with_changes(comma=MaybeSentinel.DEFAULT)

        # figure module name, may be relative so we need to handle dots
        split = re.split(r"^(\.+)", module_name)
        actual_name = split[-1]

        n_dots = 0 if len(split) == 1 else len(split[1])
        return cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=_node_from_name(actual_name) if actual_name else None,
                    names=all_ia,
                    relative=[cst.Dot()] * n_dots,
                )
            ],
            leading_lines=comments,
        )

    def _handle_from_imports(self, from_import_stmts):
        imports_dict, star_imports_dict = self._binsort_from_imports_by_module(
            from_import_stmts
        )

        new_from_import_stmts = []
        # creates the stmt for each star dict entry
        for module_name, comments in star_imports_dict.items():
            ordered_comments = list(itertools.chain.from_iterable(reversed(comments)))
            new_stmt = cst.parse_statement(f"from {module_name} import *")
            new_from_import_stmts.append(
                new_stmt.with_changes(leading_lines=ordered_comments)
            )

        # creates the stmt for each dictionary entry
        for module_name, (name_alias_set, comments) in imports_dict.items():
            ordered_comments = list(itertools.chain.from_iterable(reversed(comments)))
            new_from_import_stmts.append(
                self._create_from_import_stmt(
                    module_name, name_alias_set, ordered_comments
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
        imports_by_section = _order_sections(
            _triage_imports(
                regular_import_stmts,
                self.src_path,
            )
        )
        _sort_each_section(imports_by_section)

        from_imports_by_section = _order_sections(
            _triage_imports(
                from_import_stmts,
                self.src_path,
            )
        )
        _sort_each_section(from_imports_by_section)

        # merge regular and from imports and filter empty sections
        for i, section in enumerate(imports_by_section):
            section.extend(from_imports_by_section[i])

        imports_by_section = list(filter(lambda x: x, imports_by_section))

        # add empty lines after each section
        # for this, we add an empty line at the leading_lines of the first node at each section
        for section in imports_by_section[1:]:
            if section:
                lead = section[0]
                section[0] = lead.with_changes(
                    leading_lines=[cst.EmptyLine()] + lead.leading_lines
                )

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


def _split_leading_lines(stmt: cst.SimpleStatementLine) -> int:
    """
    For a given SimpleStatementLine, split the leading_lines nodes head and tail by index, where tail will contain the longest comment block right before the line. Returns the index where the tail starts.
    """
    i = len(stmt.leading_lines) - 1
    while i >= 0:
        empty_line = stmt.leading_lines[i]
        if not matchers.matches(
            empty_line, matchers.EmptyLine(comment=matchers.Comment())
        ):
            break
        i = i - 1
    return i + 1


def _trim_leading_lines(stmt: cst.SimpleStatementLine) -> List[cst.EmptyLine]:
    """
    For a given SimpleStatementLine, gather the list of comments right above it.
    """
    i = _split_leading_lines(stmt)
    return list(stmt.leading_lines[i:])


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
    config = Config(src_paths=(src_path,))

    sections_dict: dict[str, list[cst.SimpleStatementLine]] = defaultdict(list)
    for stmt in all_imports:
        imp = stmt.body[0]
        section = isort.place.module(_get_name(imp), config)

        sections_dict[section].append(stmt)
    return sections_dict


def _order_sections(sections, order=isort.sections.DEFAULT):
    """
    Order a dictionary of import statements organized by sections into a given order. It defaults to isort's default order.
    """
    sections_list: list[cst.SimpleStatementLine] = []
    for section in order:
        sections_list.append(sections[section])

    return sections_list


def _natural_key(s):
    """
    Converts a string into a key for natural sorting.
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()  # noqa: E731
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
        return "." * len(node.relative) + (get_full_name_for_node(node.module) or "")
    if matchers.matches(node, matchers.Import()):
        return get_full_name_for_node(node.names[0].name)
    return ""
