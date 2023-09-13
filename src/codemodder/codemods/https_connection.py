from libcst import matchers
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.helpers import get_full_name_for_node
from libcst.metadata import (
    Assignment,
    ImportAssignment,
    PositionProvider,
    ScopeProvider,
)
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.change import Change
from codemodder.file_context import FileContext
import libcst as cst
from libcst.codemod import (
    Codemod,
    CodemodContext,
    VisitorBasedCodemodCommand,
)


class HTTPSConnection(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Enforce HTTPS connection"),
        NAME="https-connection",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    CHANGE_DESCRIPTION = "Enforced HTTPS connection"

    METADATA_DEPENDENCIES = (PositionProvider, ScopeProvider)

    matching_functions = {
        "urllib3.HTTPConnectionPool",
        "urllib3.connectionpool.HTTPConnectionPool",
    }
    replacing_function = "HTTPSConnectionPool"

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, file_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = ConnectionPollVisitor(self.context, self.file_context)
        self.file_context.codemod_changes.extend(visitor.changes_in_file)
        return visitor.transform_module(tree)


class ConnectionPollVisitor(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (PositionProvider, ScopeProvider)

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        super().__init__(codemod_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include
        self.changes_in_file: list[Change] = []

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        line_number = pos_to_match.start.line
        if self.filter_by_path_includes_or_excludes(pos_to_match):
            true_name = self._get_full_true_name(original_node.func)
            if (
                self.is_call_from_imported_module(original_node)
                and true_name in HTTPSConnection.matching_functions
            ):
                self.changes_in_file.append(
                    Change(
                        str(line_number), HTTPSConnection.CHANGE_DESCRIPTION
                    ).to_json()
                )
                # TODO last argument _proxy_config needs to be converted into keyword
                # has a prefix, e.g. a.call() -> a.new_call()
                if matchers.matches(original_node.func, matchers.Attribute()):
                    return updated_node.with_changes(
                        func=updated_node.func.with_changes(
                            attr=cst.parse_expression("HTTPSConnectionPool")
                        )
                    )
                # it is a simple name, e.g. call() -> module.new_call()
                AddImportsVisitor.add_needed_import(self.context, "urllib3")
                RemoveImportsVisitor.remove_unused_import_by_node(
                    self.context, original_node
                )
                return updated_node.with_changes(
                    func=cst.parse_expression("urllib3.HTTPSConnectionPool")
                )
        return updated_node

    def _get_full_true_name(self, node):
        if matchers.matches(node, matchers.Name()):
            maybe_assignment = self.find_single_assignment(node)
            if maybe_assignment and isinstance(maybe_assignment, ImportAssignment):
                import_node = maybe_assignment.node
                for alias in import_node.names:
                    if maybe_assignment.name in (
                        alias.evaluated_alias,
                        alias.evaluated_name,
                    ):
                        return self._get_true_name_for_import(import_node, alias)
            return node.value

        if matchers.matches(node, matchers.Attribute()):
            maybe_name = self._get_full_true_name(node.value)
            if maybe_name:
                return maybe_name + "." + node.attr.value
        return None

    def _get_true_name_for_import(self, import_node, import_alias):
        """
        For import nodes, this is defined as the module name. For ImportFrom, this is defined as <module name>.<alias_name>.
        """
        if matchers.matches(import_node, matchers.Import()):
            return get_full_name_for_node(import_alias.name)
        # it is a from import
        return _get_name(import_node) + "." + get_full_name_for_node(import_alias.name)

    def is_call_from_imported_module(
        self, call: cst.Call
    ) -> tuple[cst.Import | cst.ImportFrom, cst.ImportAlias] | None:
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

    def _find_assignments(
        self, node: cst.Name | cst.Attribute | cst.Call | cst.Subscript | cst.Decorator
    ) -> set[Assignment]:
        """
        Given a MetadataWrapper and a CSTNode with a possible access to it, find all the possible assignments that it refers.
        """
        scope = self.get_metadata(ScopeProvider, node)
        # TODO workaround for a bug in libcst
        if matchers.matches(node, cst.Attribute):
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
        self, node: cst.Name | cst.Attribute
    ) -> Assignment | None:
        """
        Given a MetadataWrapper and a CSTNode representing an access, find if there is a single assignment that it refers to.
        """
        assignments = self._find_assignments(node)
        if len(assignments) == 1:
            return next(iter(assignments))
        return None

    def filter_by_path_includes_or_excludes(self, pos_to_match):
        """
        Returns False if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(PositionProvider, node)


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


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line


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
