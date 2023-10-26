from typing import Any, Optional, Tuple, Union
import libcst as cst
from libcst import MetadataDependent, matchers
from libcst.helpers import get_full_name_for_node
from libcst.metadata import (
    Assignment,
    BaseAssignment,
    ImportAssignment,
    Scope,
    ScopeProvider,
)
from libcst.metadata.scope_provider import GlobalScope


class NameResolutionMixin(MetadataDependent):
    METADATA_DEPENDENCIES: Tuple[Any, ...] = (ScopeProvider,)

    def _iterate_scope_ancestors(self, scope: Scope):
        """
        Iterate over all the ancestors of scope. Includes self.
        """
        yield scope
        while not isinstance(scope, GlobalScope):
            scope = scope.parent
            yield scope

    def find_import_alias_in_nodes_scope_from_name(self, name, node):
        maybe_tuple = self.find_import_in_nodes_scope_from_name(name, node)
        if maybe_tuple:
            return self._get_assigned_name_for_import(maybe_tuple[1])
        return None

    def _get_assigned_name_for_import(self, alias: cst.ImportAlias) -> str:
        # "" shouldn't happen in any way, sanity check
        if alias.asname:
            match name := alias.asname.name:
                case cst.Name():
                    return name.value
                case _:
                    return ""
        return get_full_name_for_node(alias.name.value) or ""

    def find_import_in_nodes_scope_from_name(
        self, name: str, node: cst.CSTNode
    ) -> Optional[Tuple[cst.ImportFrom | cst.Import, cst.ImportAlias]]:
        """
        Given a node, find the earliest import node and alias for the given name in its scope.
        """
        for scope in self._iterate_scope_ancestors(
            self.get_metadata(ScopeProvider, node)
        ):
            all_import_assignments = filter(
                lambda x: isinstance(x, ImportAssignment),
                reversed(list(scope.assignments)),
            )
            unique_import_nodes = {ia.node: None for ia in all_import_assignments}
            for imp in unique_import_nodes.keys():
                match imp:
                    case cst.Import():
                        for ia in imp.names:
                            if get_full_name_for_node(ia.name) == name:
                                return (imp, ia)
                    case cst.ImportFrom():
                        if not isinstance(imp.names, cst.ImportStar):
                            for ia in imp.names:
                                if get_full_name_for_node(ia.name) == name:
                                    return (imp, ia)
        return None

    def find_base_name(self, node):
        """
        Given a node, solve its name to its basest form. For now it can only solve names that are imported. For example, in what follows, the base name for exec.capitalize() is sys.executable.capitalize.
        from sys import executable as exec
        exec.capitalize()
        """
        if matchers.matches(node, matchers.Name()):
            maybe_assignment = self.find_single_assignment(node)
            if maybe_assignment and isinstance(maybe_assignment, ImportAssignment):
                import_node = maybe_assignment.node
                for alias in import_node.names:
                    if maybe_assignment.name in (
                        alias.evaluated_alias,
                        alias.evaluated_name,
                    ):
                        return self.base_name_for_import(import_node, alias)
            return node.value

        if matchers.matches(node, matchers.Attribute()):
            maybe_name = self.find_base_name(node.value)
            if maybe_name:
                return maybe_name + "." + node.attr.value
        return None

    def base_name_for_import(self, import_node, import_alias):
        """
        For import nodes, this is defined as the module name. For ImportFrom, this is defined as <module name>.<alias_name>.
        """
        if matchers.matches(import_node, matchers.Import()):
            return get_full_name_for_node(import_alias.name)
        # it is a from import
        return _get_name(import_node) + "." + get_full_name_for_node(import_alias.name)

    def _is_direct_call_from_imported_module(
        self, call: cst.Call
    ) -> Optional[tuple[Union[cst.Import, cst.ImportFrom], cst.ImportAlias]]:
        for nodo in iterate_left_expressions(call):
            if matchers.matches(nodo, matchers.Name() | matchers.Attribute()):
                maybe_assignment = self.find_single_assignment(nodo)
                if isinstance(maybe_assignment, ImportAssignment):
                    import_node = maybe_assignment.node
                    for alias in import_node.names:
                        if maybe_assignment.name in (
                            alias.evaluated_alias,
                            alias.evaluated_name,
                        ):
                            return (import_node, alias)
        return None

    def find_assignments(
        self,
        node: Union[cst.Name, cst.Attribute, cst.Call, cst.Subscript, cst.Decorator],
    ) -> set[BaseAssignment]:
        """
        Given a MetadataWrapper and a CSTNode with a possible access to it, find all the possible assignments that it refers.
        """
        scope = self.get_metadata(ScopeProvider, node)
        if node in scope.accesses:
            # pylint: disable=protected-access
            return set(next(iter(scope.accesses[node])).referents)
        return set()

    def find_used_names_in_module(self):
        """
        Find all the used names in the scope of a libcst Module.
        """
        names = []
        scope = self.find_global_scope()
        if scope is None:
            return []  # pragma: no cover

        nodes = [x.node for x in scope.assignments]
        for other_nodes in nodes:
            visitor = GatherNamesVisitor()
            other_nodes.visit(visitor)
            names.extend(visitor.names)
        return names

    def find_global_scope(self):
        """Find the global scope for a libcst Module node."""
        scopes = self.context.wrapper.resolve(ScopeProvider).values()
        for scope in scopes:
            if isinstance(scope, GlobalScope):
                return scope
        return None  # pragma: no cover

    def find_single_assignment(
        self,
        node: Union[cst.Name, cst.Attribute, cst.Call, cst.Subscript, cst.Decorator],
    ) -> Optional[Assignment]:
        """
        Given a MetadataWrapper and a CSTNode representing an access, find if there is a single assignment that it refers to.
        """
        assignments = self.find_assignments(node)
        if len(assignments) == 1:
            return next(iter(assignments))
        return None


def iterate_left_expressions(node: cst.BaseExpression):
    yield node
    if matchers.matches(node, matchers.Attribute()):
        yield from iterate_left_expressions(node.value)
    if matchers.matches(node, matchers.Call()):
        yield from iterate_left_expressions(node.func)


def get_leftmost_expression(node: cst.BaseExpression) -> cst.BaseExpression:
    """
    Given an expression with dots (e.g. a.b.call()), extract the leftmost expression.
    """
    if matchers.matches(node, matchers.Attribute()):
        return get_leftmost_expression(node.value)
    if matchers.matches(node, matchers.Call(func=matchers.Attribute())):
        return get_leftmost_expression(node.func)
    return node


def _get_name(node: Union[cst.Import, cst.ImportFrom]) -> str:
    """
    Get the full name of a module referenced by a Import or ImportFrom node.
    For relative modules, dots are added at the beginning
    """
    if matchers.matches(node, matchers.ImportFrom()):
        return "." * len(node.relative) + (get_full_name_for_node(node.module) or "")
    if matchers.matches(node, matchers.Import()):
        return get_full_name_for_node(node.names[0].name)
    return ""


class GatherNamesVisitor(cst.CSTVisitor):
    def __init__(self):
        self.names = []

    def visit_Name(self, node: cst.Name) -> None:
        self.names.append(node.value)
