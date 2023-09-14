from typing import Optional, Union
import libcst as cst
from libcst import MetadataDependent, matchers
from libcst.helpers import get_full_name_for_node
from libcst.metadata import Assignment, ImportAssignment, ScopeProvider


class NameResolutionMixin(MetadataDependent):
    METADATA_DEPENDENCIES = (ScopeProvider,)

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
    ) -> set[Assignment]:
        """
        Given a MetadataWrapper and a CSTNode with a possible access to it, find all the possible assignments that it refers.
        """
        scope = self.get_metadata(ScopeProvider, node)
        # TODO workaround for a bug in libcst
        if matchers.matches(node, matchers.Attribute()):
            for access in scope.accesses:
                if access.node == node:
                    # pylint: disable=protected-access
                    return access._Access__assignments
        else:
            if node in scope.accesses:
                # pylint: disable=protected-access
                return next(iter(scope.accesses[node]))._Access__assignments
        return set()

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
