from functools import partial
from typing import Optional, Sequence

import libcst as cst
from libcst import SimpleStatementLine, ensure_type, matchers
from libcst.codemod import CodemodContext, ContextAwareVisitor
from libcst.metadata import (
    BuiltinAssignment,
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils import MetadataPreservingTransformer
from codemodder.codemods.utils_mixin import (
    AncestorPatternsMixin,
    NameAndAncestorResolutionMixin,
    NameResolutionMixin,
)
from codemodder.codetf import Change
from codemodder.file_context import FileContext
from codemodder.result import Result
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class FileResourceLeakTransformer(LibcstResultTransformer):
    change_description = "Wrapped opened resource in a with statement."

    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
    )

    def __init__(
        self,
        context: CodemodContext,
        results: list[Result],
        file_context: FileContext,
        *codemod_args,
        **codemod_kwargs,
    ) -> None:
        del codemod_args
        self.changed_nodes: dict[
            cst.CSTNode, cst.CSTNode | cst.RemovalSentinel | cst.FlattenSentinel
        ] = {}
        super().__init__(context, results, file_context, **codemod_kwargs)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        fr = FindResources(self.context)
        tree.visit(fr)

        def line_filter(x):
            return self.filter_by_path_includes_or_excludes(x[2])

        for k, v in fr.assigned_resources.items():
            fr.assigned_resources[k] = [t for t in v if line_filter(t)]
        fixer = ResourceLeakFixer(
            self.context, self.file_context, fr.assigned_resources
        )
        result = tree.visit(fixer)
        self.file_context.codemod_changes.extend(fixer.changes)
        return result


FileResourceLeak = CoreCodemod(
    metadata=Metadata(
        name="fix-file-resource-leak",
        summary="Automatically Close Resources",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="https://cwe.mitre.org/data/definitions/772.html"),
            Reference(url="https://cwe.mitre.org/data/definitions/404.html"),
        ],
    ),
    transformer=LibcstTransformerPipeline(FileResourceLeakTransformer),
    detector=None,
)


class FindResources(ContextAwareVisitor, NameResolutionMixin, AncestorPatternsMixin):
    """
    Finds and all the patterns of the form x = resource(...), where resource is an call that results in an open resource. It gathers the path in the tree corresponding to the mentioned pattern.
    """

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.assigned_resources: dict[
            cst.IndentedBlock | cst.Module,
            list[
                tuple[
                    cst.SimpleStatementLine,
                    cst.Assign | cst.AnnAssign,
                    cst.Call,
                ]
            ],
        ] = {}

    def leave_SimpleStatementLine(self, original_node: cst.SimpleStatementLine) -> None:
        # Should be of the form x = resource(...)
        # i.e. IndentedBlock -> SimpleStatementLine -> Assign | AnnAssign -> Call
        match original_node:
            case cst.SimpleStatementLine(body=[bsstmt]):
                block = self.get_parent(original_node)
                # SimpleStatementLine is always part of a IndentedBlock or Module body
                block = ensure_type(block, cst.IndentedBlock | cst.Module)
                if isinstance(block, cst.Module) or self._has_no_classdef_parent(block):
                    maybe_tuple = self._is_named_assign_of_resource(bsstmt)  # type: ignore
                    if maybe_tuple:
                        assign, call = maybe_tuple
                        if block in self.assigned_resources:
                            self.assigned_resources[block].append(
                                (original_node, assign, call)
                            )
                        else:
                            self.assigned_resources[block] = [
                                (original_node, assign, call)
                            ]

    def _has_no_classdef_parent(self, block: cst.CSTNode) -> bool:
        block_parent = self.get_parent(block)
        if block_parent and not isinstance(block_parent, cst.ClassDef):
            return True
        return False

    def _is_named_assign_of_resource(
        self, bsstmt: cst.BaseSmallStatement
    ) -> Optional[tuple[cst.AnnAssign | cst.Assign, cst.Call]]:
        match bsstmt:
            case cst.Assign(value=value, targets=targets):
                maybe_value = self._is_resource_call(value)  # type: ignore
                if maybe_value and all(
                    map(
                        lambda t: matchers.matches(
                            t, matchers.AssignTarget(target=matchers.Name())
                        ),
                        targets,  # type: ignore
                    )
                ):
                    return (bsstmt, maybe_value)
            case cst.AnnAssign(target=target, value=value):
                maybe_value = self._is_resource_call(value)  # type: ignore
                if maybe_value and isinstance(target, cst.Name):  # type: ignore
                    return (bsstmt, maybe_value)
        return None

    def _is_resource_call(self, value) -> Optional[cst.Call]:
        match value:
            case cst.Call() if self._is_resource(value):
                return value
        return None

    def _is_resource(self, call: cst.Call) -> bool:
        if maybe_assignment := self.find_single_assignment(call):
            # is open call
            if isinstance(maybe_assignment, BuiltinAssignment) and matchers.matches(
                call.func, matchers.Name(value="open")
            ):
                return True
        return False


class ResourceLeakFixer(MetadataPreservingTransformer, NameAndAncestorResolutionMixin):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self,
        context: CodemodContext,
        file_context: FileContext,
        leaked_assigned_resources: dict[
            cst.IndentedBlock | cst.Module,
            list[
                tuple[
                    cst.SimpleStatementLine,
                    cst.Assign | cst.AnnAssign,
                    cst.Call,
                ]
            ],
        ],
    ):
        super().__init__(context)
        self.leaked_assigned_resources = leaked_assigned_resources
        self.changes: list[Change] = []
        self.file_context = file_context

    def _is_fixable(self, block, index, named_targets, other_targets) -> bool:
        # assigned to something that is not a Name?
        if other_targets:
            return False
        # yield, returned, argument of a call, referenced outside of block
        name_escapes_partial = partial(
            self._name_escapes_scope, block=block, index=index
        )
        # is closed?
        name_condition = map(
            lambda n: not self._is_closed(n) and not name_escapes_partial(n),
            named_targets,
        )
        return all(name_condition)

    def _handle_block(
        self,
        original_block: cst.Module | cst.IndentedBlock,
        updated_block,
        leak: list[
            tuple[cst.SimpleStatementLine, cst.Assign | cst.AnnAssign, cst.Call]
        ],
    ) -> cst.Module | cst.IndentedBlock:
        new_stmts = list(updated_block.body)
        # points to the index of the statement the original statement is now included in
        # for example, in:
        # f = open('test')
        # f.read()
        # print('stop')
        # 1 would point to 0 since f.read() would be included in the with statement of 0
        new_index_of_original_stmt = list(range(len(new_stmts)))
        for stmt, assignment, resource in reversed(leak):
            named_targets, other_targets = self.find_transitive_assignment_targets(
                resource
            )
            index = original_block.body.index(stmt)
            if self._is_fixable(original_block, index, named_targets, other_targets):
                line_number = self.get_metadata(PositionProvider, resource).start.line
                self.changes.append(
                    Change(
                        lineNumber=line_number,
                        description=FileResourceLeakTransformer.change_description,
                        findings=self.file_context.get_findings_for_location(
                            line_number
                        ),
                    )
                )

                # grab the index of the last statement with reference to the resource
                last_index = self._find_last_index_with_access(
                    named_targets, original_block, index
                )

                # No accesses, remove the statement
                if last_index is None:
                    new_stmts[index] = cst.Pass()
                    new_index_of_original_stmt[index] = -1
                    continue

                # check if the statement in the last_index is now included in some earlier with statement
                new_last_index = new_index_of_original_stmt[last_index]

                # build the with statement
                new_with = self._wrap_in_with_statement(
                    new_stmts,
                    new_index_of_original_stmt,
                    assignment,
                    resource,
                    index,
                    new_last_index,
                )
                new_stmts[index] = new_with

                # if the statement at i was included in the with statement (at index) then point it
                for i in range(index, last_index + 1):
                    new_index_of_original_stmt[i] = index

        new_block_stmts = []
        # if point != i do not include it since the statement at i is now included in the statement at point
        for i, point in enumerate(new_index_of_original_stmt):
            if point == i:
                new_block_stmts.append(new_stmts[i])
        new_block = updated_block.with_changes(body=new_block_stmts)
        return new_block

    def leave_IndentedBlock(
        self, original_node: cst.IndentedBlock, updated_node: cst.IndentedBlock
    ) -> cst.BaseSuite:
        if original_node in self.leaked_assigned_resources:
            return self._handle_block(
                original_node,
                updated_node,
                self.leaked_assigned_resources[original_node],
            )
        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node) -> cst.Module:
        if original_node in self.leaked_assigned_resources:
            return self._handle_block(
                original_node,
                updated_node,
                self.leaked_assigned_resources[original_node],
            )
        return updated_node

    def _find_last_index_with_access(
        self, named_targets, block, index
    ) -> Optional[int]:
        last_index = None
        for name in named_targets:
            accesses = self.find_accesses(name)
            for node in (access.node for access in accesses):
                last_index_for_node = (index + 1) + self._last_ancestor_index(
                    node, block.body[index + 1 :]
                )
                if not last_index or (
                    last_index_for_node and last_index_for_node > last_index
                ):
                    last_index = last_index_for_node
        return last_index

    def _last_ancestor_index(self, node, node_sequence) -> Optional[int]:
        last = None
        path = self.path_to_root_as_set(node)
        for i, n in enumerate(node_sequence):
            if n in path:
                last = i
        return last

    def _wrap_in_with_statement(
        self,
        stmts: list[SimpleStatementLine],
        stmts_index,
        assign: cst.Assign | cst.AnnAssign,
        resource: cst.Call,
        index: int,
        last_index: int,
    ) -> cst.With:
        # only include statements that were not moved into another with statement
        body_stmts = []
        for i in range(index + 1, last_index + 1):
            point = stmts_index[i]
            if i == point:
                body_stmts.append(stmts[i])
        with_statement = self._build_with_statement(assign, resource, body_stmts)
        return with_statement

    def _build_with_statement(
        self, assign: cst.Assign | cst.AnnAssign, resource: cst.Call, body
    ):
        match assign:
            case cst.Assign():
                head, *tail = assign.targets
                items = [
                    cst.WithItem(item=resource, asname=cst.AsName(name=head.target))
                ]
                for t in tail:
                    items.append(
                        cst.WithItem(item=head.target, asname=cst.AsName(name=t.target))
                    )
                return cst.With(items=items, body=cst.IndentedBlock(body=body))
            case cst.AnnAssign():
                items = [
                    cst.WithItem(item=resource, asname=cst.AsName(name=assign.target))
                ]
                return cst.With(items=items, body=cst.IndentedBlock(body=body))
        # should not get here
        return None

    def _is_closed(self, name: cst.Name) -> bool:
        """
        Checks if close is called for a given name.
        """
        accesses = self.find_accesses(name)
        for node in (a.node for a in accesses):
            # is node.close() or node.__exit__
            maybe_name = self.has_attr_called(node)
            match maybe_name:
                case cst.Name(value=value):  # type: ignore
                    if value in ("close", "__exit__"):  # type: ignore
                        return True
            if self.is_with_item(
                node
            ) or self._is_arg_of_contextlib_function_in_with_item(node):
                return True
        return False

    def _name_escapes_scope(
        self, name: cst.Name, block: cst.Module | cst.IndentedBlock, index: int
    ) -> bool:
        accesses = self.find_accesses(name)
        for node in (a.node for a in accesses):
            # returned or yielded
            if self.is_return_value(node) or self.is_yield_value(node):
                return True
            # argument of a call
            # TODO exclude calls that spawn dependent resources here...
            if self.is_argument_of_call(node):
                return True
            # out of block?
            # TODO this only looks for accesses and not assignments
            # e.g.
            # out = None
            # if True:
            #    out = x
            # will pass
            if not self._filter_ancestors(node, block.body[index:]):
                return True

        return False

    def _filter_ancestors(
        self, node: cst.CSTNode, node_sequence: Sequence[cst.CSTNode]
    ) -> list[cst.CSTNode]:
        path = self.path_to_root_as_set(node)
        return list(filter(lambda n: n in path, node_sequence))

    def _find_dependent_resources(self, resource) -> list[cst.CSTNode]:
        """
        Find all the dependent resources of a given resource. A resource S is dependent to another resource R, if closing R also closes S.
        """
        return [resource]

    def _is_arg_of_contextlib_function_in_with_item(
        self, node: cst.CSTNode
    ) -> Optional[cst.WithItem]:
        """
        Checks if the node is the argument of a contextlib function that is an item in a with statement.
        """
        maybe_parent = self.get_parent(node)
        maybe_gparent = self.get_parent(maybe_parent) if maybe_parent else None
        match maybe_gparent:
            case cst.Call(item=node):
                true_name = self.find_base_name(maybe_gparent)
                if true_name and true_name.startswith("contextlib."):
                    return self.is_with_item(maybe_gparent)
        return None
