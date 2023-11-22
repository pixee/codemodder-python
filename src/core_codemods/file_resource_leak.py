from typing import Collection, Optional, Sequence
import libcst as cst
from libcst import MetadataDependent, ensure_type, matchers
from libcst.matchers import MatcherDecoratableTransformer
from libcst.codemod import (
    Codemod,
    CodemodContext,
    ContextAwareVisitor,
)
from libcst.metadata import (
    Access,
    BuiltinAssignment,
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)
from codemodder.change import Change
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.file_context import FileContext
from functools import partial


class MetadataPreservingTransformer(
    MatcherDecoratableTransformer, cst.MetadataDependent
):
    """
    The CSTTransformer equivalent of ContextAwareVisitor. Will preserve metadata passed through a context. You should not chain more than one of these, otherwise metadata will not reflect the state of the tree.
    """

    def __init__(self, context: CodemodContext) -> None:
        MetadataDependent.__init__(self)
        MatcherDecoratableTransformer.__init__(self)
        self.context = context
        dependencies = self.get_inherited_dependencies()
        if dependencies:
            wrapper = self.context.wrapper
            if wrapper is None:
                # pylint: disable-next=broad-exception-raised
                raise Exception(
                    f"Attempting to instantiate {self.__class__.__name__} outside of "
                    + "an active transform. This means that metadata hasn't been "
                    + "calculated and we cannot successfully create this visitor."
                )
            for dep in dependencies:
                if dep not in wrapper._metadata:
                    # pylint: disable-next=broad-exception-raised
                    raise Exception(
                        f"Attempting to access metadata {dep.__name__} that was not a "
                        + "declared dependency of parent transform! This means it is "
                        + "not possible to compute this value. Please ensure that all "
                        + f"parent transforms of {self.__class__.__name__} declare "
                        + f"{dep.__name__} as a metadata dependency."
                    )
            self.metadata = {dep: wrapper._metadata[dep] for dep in dependencies}


class FileResourceLeak(BaseCodemod, UtilsMixin, Codemod):
    SUMMARY = "Automatically close resources"
    METADATA = CodemodMetadata(
        DESCRIPTION=SUMMARY,
        NAME="file-resource-leak",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        REFERENCES=[
            {
                "url": "https://cwe.mitre.org/data/definitions/772.html",
                "description": "",
            },
            {
                "url": "https://cwe.mitre.org/data/definitions/404.html",
                "description": "",
            },
        ],
    )
    CHANGE_DESCRIPTION = "Wrapped opened resource in a with statement."

    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        ParentNodeProvider,
    )

    def __init__(
        self,
        context: CodemodContext,
        file_context: FileContext,
        *codemod_args,
    ) -> None:
        self.changed_nodes: dict[
            cst.CSTNode, cst.CSTNode | cst.RemovalSentinel | cst.FlattenSentinel
        ] = {}
        BaseCodemod.__init__(self, file_context, *codemod_args)
        UtilsMixin.__init__(self, [])
        Codemod.__init__(self, context)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        fr = FindResources(self.context)
        tree.visit(fr)
        line_filter = lambda x: self.filter_by_path_includes_or_excludes(x[3])
        filtered_resources = [
            resource for resource in fr.assigned_resources if line_filter(resource)
        ]
        fixer = ResourceLeakFixer(self.context, filtered_resources)
        result = tree.visit(fixer)
        self.file_context.codemod_changes.extend(fixer.changes)
        return result


class FindResources(ContextAwareVisitor, NameResolutionMixin):
    """
    Finds and all the patterns of the form x = resource(...), where resource is an call that results in an open resource. It gathers the path in the tree corresponding to the mentioned pattern.
    """

    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.assigned_resources: list[
            tuple[
                cst.IndentedBlock | cst.Module,
                cst.SimpleStatementLine,
                cst.Assign | cst.AnnAssign,
                cst.Call,
            ]
        ] = []

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
                        self.assigned_resources.append(
                            (block, original_node, assign, call)
                        )

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
        maybe_assignment = self.find_single_assignment(call)
        if maybe_assignment:
            # is open call
            if isinstance(maybe_assignment, BuiltinAssignment) and matchers.matches(
                call.func, matchers.Name(value="open")
            ):
                return True
        return False

    def get_parent(self, node: cst.CSTNode) -> Optional[cst.CSTNode]:
        try:
            return self.get_metadata(ParentNodeProvider, node, None)
        except Exception:
            pass
        return None


class ResourceLeakFixer(MetadataPreservingTransformer, NameResolutionMixin):
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        ParentNodeProvider,
    )

    def __init__(
        self,
        context: CodemodContext,
        leaked_assigned_resources: list[
            tuple[
                cst.IndentedBlock | cst.Module,
                cst.SimpleStatementLine,
                cst.Assign | cst.AnnAssign,
                cst.Call,
            ]
        ],
    ):
        super().__init__(context)
        self.leaked_assigned_resources = leaked_assigned_resources
        self.changes: list[Change] = []

    def leave_Module(self, original_node: cst.Module, updated_node) -> cst.Module:
        result = original_node
        # TODO for now it assumes no dependent resources, it won't do anything if one exists
        for (
            block,
            stmt,
            assignment,
            resource,
        ) in self.leaked_assigned_resources:
            index = block.body.index(stmt)
            named_targets, other_targets = self._find_transitive_assignment_targets(
                resource
            )
            # assigned to something that is not a Name?
            if other_targets:
                break
            # yield, returned, argument of a call, referenced outside of block
            name_escapes_partial = partial(
                self._name_escapes_scope, block=block, index=index
            )
            # is closed?
            name_condition = map(
                # pylint: disable-next=cell-var-from-loop
                lambda n: not self._is_closed(n) and not name_escapes_partial(n),
                named_targets,
            )
            if all(name_condition):
                line_number = self.get_metadata(PositionProvider, resource).start.line
                self.changes.append(
                    Change(line_number, FileResourceLeak.CHANGE_DESCRIPTION)
                )
                last_index = self._find_last_index_with_access(
                    named_targets, block, index
                )
                new_block = self._wrap_in_with_statement(
                    block, assignment, resource, index, last_index
                )
                result = result.deep_replace(block, new_block)

        return result

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

    def _find_direct_name_assignment_targets(
        self, name: cst.Name
    ) -> list[cst.BaseAssignTargetExpression]:
        name_targets = []
        accesses = self.find_accesses(name)
        for node in (access.node for access in accesses):
            maybe_assigned = self.is_value_of_assignment(node)
            if maybe_assigned:
                targets = self._extract_targets_of_assignment(maybe_assigned)
                name_targets.extend(targets)
        return name_targets

    def _find_name_assignment_targets(
        self, name: cst.Name
    ) -> tuple[list[cst.Name], list[cst.BaseAssignTargetExpression]]:
        named_targets, other_targets = self._sieve_targets(
            self._find_direct_name_assignment_targets(name)
        )

        for child in named_targets:
            c_named_targets, c_other_targets = self._find_name_assignment_targets(child)
            named_targets.extend(c_named_targets)
            other_targets.extend(c_other_targets)
        return named_targets, other_targets

    def _sieve_targets(
        self, targets
    ) -> tuple[list[cst.Name], list[cst.BaseAssignTargetExpression]]:
        named_targets = []
        other_targets = []
        for t in targets:
            # TODO maybe consider subscript here for named_targets
            if isinstance(t, cst.Name):
                named_targets.append(t)
            else:
                other_targets.append(t)
        return named_targets, other_targets

    def _find_transitive_assignment_targets(
        self, expr
    ) -> tuple[list[cst.Name], list[cst.BaseAssignTargetExpression]]:
        maybe_assigned = self.is_value_of_assignment(expr)
        if maybe_assigned:
            named_targets, other_targets = self._sieve_targets(
                self._extract_targets_of_assignment(maybe_assigned)
            )
            for n in named_targets:
                n_named_targets, n_other_targets = self._find_name_assignment_targets(n)
                named_targets.extend(n_named_targets)
                other_targets.extend(n_other_targets)
            return named_targets, other_targets
        return ([], [])

    def _extract_targets_of_assignment(
        self, assignment: cst.AnnAssign | cst.Assign | cst.WithItem | cst.NamedExpr
    ) -> list[cst.BaseExpression]:
        match assignment:
            case cst.AnnAssign():
                if assignment.target:
                    return [assignment.target]
            case cst.Assign():
                return [t.target for t in assignment.targets]
            case cst.NamedExpr():
                return [assignment.target]
            case cst.WithItem():
                if assignment.asname:
                    return [assignment.asname.name]
        return []

    # pylint: disable-next=too-many-arguments
    def _wrap_in_with_statement(
        self,
        block: cst.Module | cst.IndentedBlock,
        assign: cst.Assign | cst.AnnAssign,
        resource: cst.Call,
        index: int,
        last_index: Optional[int] = None,
    ) -> cst.Module | cst.IndentedBlock:
        block_body = block.body
        if last_index:
            with_statements = block_body[index + 1 : last_index + 1]
            trailing_statements = block_body[last_index + 1 :]
        else:
            with_statements = block_body[index + 1 :]
            trailing_statements = []
        with_statement = self._build_with_statement(assign, resource, with_statements)
        new_body = [*block_body[:index], with_statement, *trailing_statements]
        return block.with_changes(body=new_body)

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
            ancestors = self._filter_ancestors(node, block.body[index:])
            # TODO this only looks for accesses and not assignments
            # e.g.
            # out = None
            # if True:
            #    out = x
            # will pass
            if not ancestors:
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

    def find_accesses(self, node) -> Collection[Access]:
        scope = self.get_metadata(ScopeProvider, node, None)
        if scope:
            return scope.accesses[node]
        return {}

    def is_value_of_assignment(
        self, expr
    ) -> Optional[cst.AnnAssign | cst.Assign | cst.WithItem | cst.NamedExpr]:
        """
        Tests if expr is the value in an assignment.
        """
        parent = self.get_metadata(ParentNodeProvider, expr)
        match parent:
            case cst.AnnAssign(value=value) | cst.Assign(value=value) | cst.WithItem(
                item=value
            ) | cst.NamedExpr(
                value=value
            ) if expr == value:  # type: ignore
                return parent
        return None

    def has_attr_called(self, node: cst.CSTNode) -> Optional[cst.Name]:
        """
        Checks if node is part of an expression of the form: <node>.call().
        """
        maybe_attr = self.is_attribute_value(node)
        maybe_call = self.is_call_func(maybe_attr) if maybe_attr else None
        if maybe_attr and maybe_call:
            return maybe_attr.attr
        return None

    def is_argument_of_call(self, node: cst.CSTNode) -> Optional[cst.Arg]:
        """
        Checks if the node is an argument of a call.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.Arg(value=node):
                return maybe_parent
        return None

    def is_yield_value(self, node: cst.CSTNode) -> Optional[cst.Yield]:
        """
        Checks if the node is the value of a Yield statement.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.Yield(value=node):
                return maybe_parent
        return None

    def is_return_value(self, node: cst.CSTNode) -> Optional[cst.Return]:
        """
        Checks if the node is the value of a Return statement.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.Return(value=node):
                return maybe_parent
        return None

    def is_with_item(self, node: cst.CSTNode) -> Optional[cst.WithItem]:
        """
        Checks if the node is the name of a WithItem.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.WithItem(item=node):
                return maybe_parent
        return None

    def is_call_func(self, node: cst.CSTNode) -> Optional[cst.Call]:
        """
        Checks if the node is the func of an Call.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.Call(func=node):
                return maybe_parent
        return None

    def is_attribute_value(self, node: cst.CSTNode) -> Optional[cst.Attribute]:
        """
        Checks if node is the value of an Attribute.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.Attribute(value=node):
                return maybe_parent
        return None

    def path_to_root(self, node: cst.CSTNode) -> list[cst.CSTNode]:
        """
        Returns node's path to root. Includes self.
        """
        path = []
        maybe_parent = node
        while maybe_parent:
            path.append(maybe_parent)
            maybe_parent = self.get_parent(maybe_parent)
        return path

    def path_to_root_as_set(self, node: cst.CSTNode) -> set[cst.CSTNode]:
        """
        Returns the set of nodes in node's path to root. Includes self.
        """
        path = set()
        maybe_parent = node
        while maybe_parent:
            path.add(maybe_parent)
            maybe_parent = self.get_parent(maybe_parent)
        return path

    def is_ancestor(self, node: cst.CSTNode, other_node: cst.CSTNode) -> bool:
        """
        Tests if other_node is an ancestor of node in the CST.
        """
        path = self.path_to_root_as_set(node)
        return other_node in path

    def get_parent(self, node: cst.CSTNode) -> Optional[cst.CSTNode]:
        """
        Retrieves the parent of node. Will return None for the root.
        """
        try:
            return self.get_metadata(ParentNodeProvider, node, None)
        except Exception:
            pass
        return None
