import itertools
from typing import ClassVar, Collection, Optional, Union

import libcst as cst
from libcst import MetadataDependent, matchers
from libcst.helpers import get_full_name_for_node
from libcst.metadata import (
    Access,
    Assignment,
    BaseAssignment,
    BuiltinAssignment,
    ImportAssignment,
    ParentNodeProvider,
    ProviderT,
    Scope,
    ScopeProvider,
)
from libcst.metadata.scope_provider import GlobalScope

from codemodder.utils.utils import extract_targets_of_assignment


class NameResolutionMixin(MetadataDependent):
    METADATA_DEPENDENCIES: ClassVar[Collection[ProviderT]] = (ScopeProvider,)

    def _find_imported_name(self, node: cst.Name) -> Optional[str]:
        match self.find_single_assignment(node):
            case ImportAssignment(
                name=node.value,
                node=(
                    cst.Import(names=names) | cst.ImportFrom(names=names)
                ) as import_node,
            ) as assignment:
                match names:
                    case cst.ImportStar():
                        return node.value

                for alias in names:
                    if assignment.name in (
                        alias.evaluated_alias,
                        alias.evaluated_name,
                    ):
                        return self.base_name_for_import(import_node, alias)
            case BuiltinAssignment():
                return "builtins." + node.value

        return node.value

    def find_base_name(self, node) -> Optional[str]:
        """
        Given a node, resolve its name to its basest form.

        For now it can only solve names that are imported. For example, in what
        follows, the base name for exec.capitalize() is sys.executable.capitalize.

        ```
        from sys import executable as exec
        exec.capitalize()
        ```
        """
        match node:
            case cst.Name():
                return self._find_imported_name(node)

            case cst.Attribute():
                if maybe_name := self.find_base_name(node.value):
                    return maybe_name + "." + node.attr.value

            case cst.Call():
                return self.find_base_name(node.func)
        return None

    def find_alias_for_import_in_node(self, import_name, node) -> Optional[str]:
        """
        Check if the node uses an imported alias for import_name.
        """
        match node:
            case cst.Name():
                maybe_assignment = self.find_single_assignment(node)
                if maybe_assignment and isinstance(maybe_assignment, ImportAssignment):
                    import_node = maybe_assignment.node
                    for alias in import_node.names:
                        if alias.evaluated_name == import_name:
                            return alias.evaluated_alias

            case cst.Attribute():
                return self.find_alias_for_import_in_node(import_name, node.value)

            case cst.Call():
                return self.find_alias_for_import_in_node(import_name, node.func)

        return None

    def base_name_for_import(self, import_node, import_alias):
        """
        For import nodes, this is defined as the module name. For ImportFrom, this is defined as <module name>.<alias_name>.
        """
        if matchers.matches(import_node, matchers.Import()):
            return get_full_name_for_node(import_alias.name)
        # it is a from import
        return _get_name(import_node) + "." + get_full_name_for_node(import_alias.name)

    def is_direct_call_from_imported_module(
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

    def get_imported_prefix(
        self, node
    ) -> Optional[tuple[Union[cst.Import, cst.ImportFrom], cst.ImportAlias]]:
        """
        Given a node representing an access, finds if any part of its prefix is imported.
        Returns a import and import alias pair.
        """
        for nodo in iterate_left_expressions(node):
            match nodo:
                case cst.Name() | cst.Attribute():
                    maybe_assignment = self.find_single_assignment(nodo)
                    if maybe_assignment and isinstance(
                        maybe_assignment, ImportAssignment
                    ):
                        import_node = maybe_assignment.node
                        for alias in import_node.names:
                            if maybe_assignment.name in (
                                alias.evaluated_alias,
                                alias.evaluated_name,
                            ):
                                return (import_node, alias)
        return None

    def get_aliased_prefix_name_from_import(
        self, import_alias: cst.ImportAlias, name: str
    ) -> Optional[str]:
        """
        Returns the alias name, otherwise just name, of the given import if its name matches name.
        """
        maybe_name = None
        if (imp_name := get_full_name_for_node(import_alias.name)) == name:
            # AsName is always a Name for ImportAlias
            maybe_name = (
                import_alias.asname.name.value if import_alias.asname else imp_name
            )
        return maybe_name

    def get_aliased_prefix_name(self, node: cst.CSTNode, name: str) -> Optional[str]:
        """
        Returns the alias of name, or just name itself, if name is imported and used as a prefix for this node.
        """
        maybe_import = self.get_imported_prefix(node)
        if maybe_import and matchers.matches(maybe_import[0], matchers.Import()):
            _, ia = maybe_import
            return self.get_aliased_prefix_name_from_import(ia, name)
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
            return set(next(iter(scope.accesses[node])).referents)
        return set()

    def generate_available_name(self, node, preference: list[str]) -> str:
        """
        Generate an available name within node's scope. It will check for availability the names of a given list in order. If the list is exausted, returns the first name of the form {name}_{count} such that name is the first name in the preference list.
        """
        used_names = self.find_used_names_within_nodes_scope(node)
        for name in preference:
            if name not in used_names:
                return name
        count = 1
        name = preference[0] + f"_{count}"
        while name in used_names:
            count += 1
            name = preference[0] + f"_{count}"
        return name

    def find_used_names_in_module(self):
        """
        Find all the used names in the scope of a libcst Module.
        """
        names = []
        if (scope := self.find_global_scope()) is None:
            return []  # pragma: no cover

        nodes = [x.node for x in scope.assignments]
        for other_nodes in nodes:
            visitor = GatherNamesVisitor()
            other_nodes.visit(visitor)
            names.extend(visitor.names)
        return names

    def find_used_names_within_nodes_scope(self, node: cst.CSTNode) -> set[str]:
        """
        Find all the names used within all the ancestor and descendent scopes of a given node's scope.
        """
        # TODO support for global and nonlocal statements
        scope = self.get_metadata(ScopeProvider, node, None)
        return self.find_used_names_within_scope(scope) if scope else set()

    def find_used_names_within_scope(self, scope: Scope) -> set[str]:
        """
        Find all the names used within all the ancestor and descendent scopes for a given scope.
        """
        related = itertools.chain(
            self._find_ancestor_scopes(scope), self._find_descendent_scopes(scope)
        )
        names: set[str] = set()
        for s in related:
            names.update(self._find_used_names_scope_only(s))
        return names

    def _find_ancestor_scopes(self, scope: Scope) -> set[Scope]:
        ancestors: set[Scope] = {scope}
        current = scope
        while not isinstance(current, GlobalScope):
            current = current.parent
            ancestors.add(current)
        return ancestors

    def _build_scopes_child_tree(self) -> dict[Scope, list[Scope]]:
        all_scopes = {
            scope
            for scope in self.context.wrapper.resolve(ScopeProvider).values()
            if scope
        }
        tree: dict[Scope, list[Scope]] = {k: [] for k in all_scopes if k}
        for s in all_scopes:
            if not isinstance(s, GlobalScope):
                tree.get(s.parent, []).append(s)
        return tree

    def _find_descendent_scopes(self, scope: Scope):
        tree = self._build_scopes_child_tree()
        descendents = set()
        stack = [scope]
        while stack:
            current = stack.pop()
            descendents.update(tree[current])
            stack.extend(tree[current])
        return descendents

    def _find_used_names_scope_only(self, scope: Scope) -> set[str]:
        return {ass.name for ass in scope.assignments}

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
    ) -> Optional[BaseAssignment]:
        """
        Given a MetadataWrapper and a CSTNode representing an access, find if there is a single assignment that it refers to.
        """
        assignments = self.find_assignments(node)
        if len(assignments) == 1:
            return next(iter(assignments))
        return None

    def is_builtin_function(self, node: cst.Call):
        """
        Given a `Call` node, find if it refers to a builtin function
        """
        maybe_assignment = self.find_single_assignment(node)
        if maybe_assignment and isinstance(maybe_assignment, BuiltinAssignment):
            return matchers.matches(node.func, matchers.Name())
        return False

    def is_staticmethod(self, node: cst.FunctionDef) -> bool:
        for decorator in node.decorators:
            if self.find_base_name(decorator.decorator) == "builtins.staticmethod":
                return True
        return False

    def is_classmethod(self, node: cst.FunctionDef) -> bool:
        for decorator in node.decorators:
            if self.find_base_name(decorator.decorator) == "builtins.classmethod":
                return True
        return False

    def find_accesses(self, node) -> Collection[Access]:
        if scope := self.get_metadata(ScopeProvider, node, None):
            return scope.accesses[node]
        return {}

    def class_has_method(self, classdef: cst.ClassDef, method_name: str) -> bool:
        """Check if a given class definition implements a method of name `method_name`."""
        for node in classdef.body.body:
            match node:
                case cst.FunctionDef(
                    name=cst.Name(value=value)
                ) if value == method_name:
                    return True
        return False


class AncestorPatternsMixin(MetadataDependent):
    METADATA_DEPENDENCIES: ClassVar[Collection[ProviderT]] = (ParentNodeProvider,)

    def is_value_of_assignment(
        self, expr
    ) -> Optional[cst.AnnAssign | cst.Assign | cst.WithItem | cst.NamedExpr]:
        """
        Tests if expr is the value in an assignment.
        """
        parent = self.get_metadata(ParentNodeProvider, expr)
        match parent:
            case (
                cst.AnnAssign(value=value)
                | cst.Assign(value=value)
                | cst.WithItem(item=value)
                | cst.NamedExpr(value=value)
            ) if expr == value:  # type: ignore
                return parent
        return None

    def is_target_of_assignment(
        self, expr
    ) -> Optional[cst.AnnAssign | cst.Assign | cst.WithItem | cst.NamedExpr]:
        """
        Tests if expr is the value in an assignment.
        """
        parent = self.get_metadata(ParentNodeProvider, expr)
        parent = parent if isinstance(parent, cst.AssignTarget) else None
        gparent = self.get_metadata(ParentNodeProvider, parent) if parent else None
        match gparent:
            case cst.AnnAssign() | cst.Assign() | cst.WithItem() | cst.NamedExpr():
                return gparent
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

    def is_subscript_value(self, node: cst.CSTNode) -> Optional[cst.Subscript]:
        """
        Checks if node is the value of an Attribute.
        """
        maybe_parent = self.get_parent(node)
        match maybe_parent:
            case cst.Subscript(value=node):
                return maybe_parent
        return None

    def find_immediate_function_def(
        self, node: cst.CSTNode
    ) -> Optional[cst.FunctionDef]:
        """
        Find if node is inside a function definition. In case of nested functions it returns the most immediate one.
        """
        # We disregard nested functions, we consider only the immediate one
        ancestors = self.path_to_root(node)
        first_fdef = None
        for ancestor in ancestors:
            if isinstance(ancestor, cst.FunctionDef):
                first_fdef = ancestor
                break
        return first_fdef

    def find_immediate_class_def(self, node: cst.CSTNode) -> Optional[cst.ClassDef]:
        """
        Find if node is inside a class definition. In case of nested classes, it returns the most immediate one.
        """
        # We disregard nested classes, we consider only the immediate one
        ancestors = self.path_to_root(node)
        first_cdef = None
        for ancestor in ancestors:
            if isinstance(ancestor, cst.ClassDef):
                first_cdef = ancestor
                break
        return first_cdef

    def path_to_root(self, node: cst.CSTNode) -> list[cst.CSTNode]:
        """
        Returns node's path to `node` (excludes `node`).
        """
        path = []
        maybe_parent = self.get_parent(node)
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


class NameAndAncestorResolutionMixin(NameResolutionMixin, AncestorPatternsMixin):

    def extract_value(
        self, node: cst.AnnAssign | cst.Assign | cst.WithItem | cst.NamedExpr
    ):
        match node:
            case (
                cst.AnnAssign(value=value)
                | cst.Assign(value=value)
                | cst.WithItem(item=value)
                | cst.NamedExpr(value=value)
            ):
                return value
        return None

    def resolve_expression(self, node: cst.BaseExpression) -> cst.BaseExpression:
        """
        If the expression is a Name, transitively resolves the name to another expression through single assignments. Otherwise returns self.
        """
        maybe_expr = None
        match node:
            case cst.Name():
                if maybe_expr := self._resolve_name_transitive(node):
                    return maybe_expr
        return node

    def _resolve_name_transitive(self, node: cst.Name) -> Optional[cst.BaseExpression]:
        maybe_assignment = self.find_single_assignment(node)
        if maybe_assignment and isinstance(maybe_assignment, Assignment):
            if maybe_target_assignment := self.is_target_of_assignment(
                maybe_assignment.node
            ):
                value = self.extract_value(maybe_target_assignment)
                match value:
                    case cst.Name():
                        return self._resolve_name_transitive(value)
                    case _:
                        return value
        return node

    def _find_direct_name_assignment_targets(
        self, name: cst.Name
    ) -> list[cst.BaseAssignTargetExpression]:
        name_targets = []
        accesses = self.find_accesses(name)
        for node in (access.node for access in accesses):
            if maybe_assigned := self.is_value_of_assignment(node):
                targets = extract_targets_of_assignment(maybe_assigned)
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

    def find_transitive_assignment_targets(
        self, expr
    ) -> tuple[list[cst.Name], list[cst.BaseAssignTargetExpression]]:
        """
        Returns all the targets that an expression can reach. It returns a pair of lists, where the first list contains all targets that are Name, and the second contains all others.
        """
        if maybe_assigned := self.is_value_of_assignment(expr):
            named_targets, other_targets = self._sieve_targets(
                extract_targets_of_assignment(maybe_assigned)
            )
            for n in named_targets:
                n_named_targets, n_other_targets = self._find_name_assignment_targets(n)
                named_targets.extend(n_named_targets)
                other_targets.extend(n_other_targets)
            return named_targets, other_targets
        return ([], [])

    def _resolve_starred_element(self, element: cst.StarredElement):
        resolved = self.resolve_expression(element.value)
        match resolved:
            case cst.List():
                return self.resolve_list_literal(resolved)
        return [element]

    def _resolve_list_element(self, element: cst.BaseElement):
        match element:
            case cst.Element():
                return [self.resolve_expression(element.value)]
            case cst.StarredElement():
                return self._resolve_starred_element(element)
        return []

    def resolve_list_literal(
        self, list_literal: cst.List
    ) -> itertools.chain[cst.BaseExpression]:
        """
        Returns an iterable of all the elements of that list resolved. It will recurse into starred elements whenever possible.
        """
        return itertools.chain.from_iterable(
            map(self._resolve_list_element, list_literal.elements)
        )

    def _resolve_starred_dict_element(self, element: cst.StarredDictElement):
        resolved = self.resolve_expression(element.value)
        match resolved:
            case cst.Dict():
                return self.resolve_dict(resolved)
        return dict()

    def _resolve_dict_element(self, element: cst.BaseDictElement):
        match element:
            case cst.StarredDictElement():
                return self._resolve_starred_dict_element(element)
            case _:
                resolved_key = self.resolve_expression(element.key)
                resolved_key_value = resolved_key
                resolved_value = self.resolve_expression(element.value)
                return {resolved_key_value: resolved_value}

    def resolve_dict(self, dictionary: cst.Dict):
        return {
            k: v
            for e in dictionary.elements
            for k, v in self._resolve_dict_element(e).items()
        }

    def _transform_string_elements(self, expr):
        match expr:
            case cst.SimpleString():
                return expr.raw_value
        return expr

    def resolve_keyword_args(self, call: cst.Call):
        """
        Returns a dict with all the keyword arguments resolved. It will recurse into starred elements whenever possible and string keys from double starred dict arguments will be converted into their raw_value.
        """
        keyword_to_expr_dict: dict = dict()
        for arg in call.args:
            if arg.star == "**":
                resolved = self.resolve_expression(arg.value)
                match resolved:
                    case cst.Dict():
                        resolved_starred_element = self.resolve_dict(resolved)
                        keyword_to_expr_dict |= {
                            self._transform_string_elements(k): v
                            for k, v in resolved_starred_element.items()
                        }
            if arg.keyword:
                keyword_to_expr_dict |= {
                    arg.keyword.value: self.resolve_expression(arg.value)
                }
        return keyword_to_expr_dict


def iterate_left_expressions(node: cst.BaseExpression):
    yield node
    match node:
        case cst.Attribute():
            yield from iterate_left_expressions(node.value)
        case cst.Call():
            yield from iterate_left_expressions(node.func)
        case cst.Subscript():
            yield from iterate_left_expressions(node.value)


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
