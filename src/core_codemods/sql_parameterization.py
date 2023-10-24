import re
from typing import Optional, Tuple
import libcst as cst
from libcst import SimpleWhitespace, matchers
from libcst.codemod import Codemod, CodemodContext, ContextAwareVisitor
from libcst.metadata import (
    ClassScope,
    GlobalScope,
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
from codemodder.codemods.transformations.remove_empty_string_concatenation import (
    RemoveEmptyStringConcatenation,
)
from codemodder.codemods.utils import Append, ReplaceNodes, get_function_name_node
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext

parameter_token = "?"

literal_number = matchers.Integer() | matchers.Float() | matchers.Imaginary()
literal_string = matchers.SimpleString()
literal = literal_number | literal_string


class SQLQueryParameterization(BaseCodemod, UtilsMixin, Codemod):
    SUMMARY = "Parameterize SQL queries."
    METADATA = CodemodMetadata(
        DESCRIPTION=SUMMARY,
        NAME="sql-parameterization",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        REFERENCES=[
            {
                "url": "https://cwe.mitre.org/data/definitions/89.html",
                "description": "",
            },
            {
                "url": "https://owasp.org/www-community/attacks/SQL_Injection",
                "description": "",
            },
        ],
    )
    CHANGE_DESCRIPTION = "Parameterized SQL query execution."

    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        ParentNodeProvider,
    )

    def __init__(
        self,
        context: CodemodContext,
        execution_context: CodemodExecutionContext,
        file_context: FileContext,
        *codemod_args,
    ) -> None:
        self.changed_nodes: dict[
            cst.CSTNode, cst.CSTNode | cst.RemovalSentinel | cst.FlattenSentinel
        ] = {}
        BaseCodemod.__init__(self, execution_context, file_context, *codemod_args)
        UtilsMixin.__init__(self, context, {})
        Codemod.__init__(self, context)

    def _build_param_element(self, middle, index: int) -> cst.BaseExpression:
        # TODO maybe a parameterized string would be better here
        # f-strings need python 3.6 though
        if index == 0:
            return middle[0]
        operator = cst.Add(
            whitespace_after=cst.SimpleWhitespace(" "),
            whitespace_before=cst.SimpleWhitespace(" "),
        )
        return cst.BinaryOperation(
            operator=operator,
            left=self._build_param_element(middle, index - 1),
            right=middle[index],
        )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        find_queries = FindQueryCalls(self.context)
        tree.visit(find_queries)

        result = tree
        for call, query in find_queries.calls.items():
            # filter by line includes/excludes
            call_pos = self.node_position(call)
            if not self.filter_by_path_includes_or_excludes(call_pos):
                break

            ep = ExtractParameters(self.context, query)
            tree.visit(ep)

            # build tuple elements and fix injection
            params_elements: list[cst.Element] = []
            for start, middle, end in ep.injection_patterns:
                # TODO support for elements from f-strings?
                # reminder that python has no implicit conversion while concatenating with +, might need to use str() for a particular expression
                expr = self._build_param_element(middle, len(middle) - 1)
                params_elements.append(
                    cst.Element(
                        value=expr,
                        comma=cst.Comma(whitespace_after=SimpleWhitespace(" ")),
                    )
                )
                self._fix_injection(start, middle, end)

            # TODO research if named parameters are widely supported
            # it could solve for the case of existing parameters
            if params_elements:
                tuple_arg = cst.Arg(cst.Tuple(elements=params_elements))
                # self.changed_nodes[call] = call.with_changes(args=[*call.args, tuple_arg])
                self.changed_nodes[call] = {"args": Append([tuple_arg])}

            # made changes
            if self.changed_nodes:
                result = result.visit(ReplaceNodes(self.changed_nodes))
                self.changed_nodes = {}
                line_number = self.get_metadata(PositionProvider, call).start.line
                self.file_context.codemod_changes.append(
                    Change(
                        str(line_number), SQLQueryParameterization.CHANGE_DESCRIPTION
                    ).to_json()
                )
                result = result.visit(RemoveEmptyStringConcatenation())

        return result

    def _fix_injection(
        self, start: cst.CSTNode, middle: list[cst.CSTNode], end: cst.CSTNode
    ):
        for expr in middle:
            self.changed_nodes[expr] = cst.parse_expression('""')
        # remove quote literal from end
        match end:
            case cst.SimpleString():
                current_end = self.changed_nodes.get(end) or end
                if current_end.raw_value.startswith("\\'"):
                    new_raw_value = current_end.raw_value[2:]
                else:
                    new_raw_value = current_end.raw_value[1:]
                new_value = (
                    current_end.prefix
                    + current_end.quote
                    + new_raw_value
                    + current_end.quote
                )
                self.changed_nodes[end] = current_end.with_changes(value=new_value)
            case cst.FormattedStringText():
                # TODO formatted string case
                pass

        # remove quote literal from start
        match start:
            case cst.SimpleString():
                current_start = self.changed_nodes.get(start) or start
                if current_start.raw_value.endswith("\\'"):
                    new_raw_value = current_start.raw_value[:-2] + parameter_token
                else:
                    new_raw_value = current_start.raw_value[:-1] + parameter_token
                new_value = (
                    current_start.prefix
                    + current_start.quote
                    + new_raw_value
                    + current_start.quote
                )
                self.changed_nodes[start] = current_start.with_changes(value=new_value)
            case cst.FormattedStringText():
                # TODO formatted string case
                pass


class LinearizeQuery(ContextAwareVisitor, NameResolutionMixin):
    """
    Gather all the expressions that are concatenated to build the query.
    """

    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, context) -> None:
        super().__init__(context)
        self.leaves: list[cst.CSTNode] = []

    def on_visit(self, node: cst.CSTNode):
        # TODO function to detect if BinaryExpression results in a number or list?
        # will it only matter inside fstrings? (outside it, we expect query to be string)
        # check if any is a string should be necessary

        # We only care about expressions, ignore everything else
        # Mostly as a sanity check, this may not be necessary since we start the visit with an expression node
        if isinstance(
            node,
            (
                cst.BaseExpression,
                cst.FormattedStringExpression,
                cst.FormattedStringText,
            ),
        ):
            # These will be the only types that will be properly visited
            if not matchers.matches(
                node,
                matchers.Name()
                | matchers.BinaryOperation()
                | matchers.FormattedString()
                | matchers.FormattedStringExpression()
                | matchers.ConcatenatedString(),
            ):
                self.leaves.append(node)
            else:
                return super().on_visit(node)
        return False

    # recursive search
    def visit_Name(self, node: cst.Name) -> Optional[bool]:
        self.leaves.extend(self.recurse_Name(node))
        return False

    def visit_Attribute(self, node: cst.Attribute) -> Optional[bool]:
        self.leaves.append(node)
        return False

    def recurse_Name(self, node: cst.Name) -> list[cst.CSTNode]:
        assignment = self.find_single_assignment(node)
        if assignment:
            base_scope = assignment.scope
            # TODO make this check in detect injection, to be more precise

            # Ensure that this variable is not used anywhere else
            # variables used in the global scope / class scope may be referenced in other files
            if (
                not isinstance(base_scope, GlobalScope)
                and not isinstance(base_scope, ClassScope)
                and len(assignment.references) == 1
            ):
                maybe_gparent = self._find_gparent(assignment.node)
                if gparent := maybe_gparent:
                    match gparent:
                        case cst.AnnAssign() | cst.Assign():
                            if gparent.value:
                                gparent_scope = self.get_metadata(
                                    ScopeProvider, gparent
                                )
                                if gparent_scope and gparent_scope == base_scope:
                                    visitor = LinearizeQuery(self.context)
                                    gparent.value.visit(visitor)
                                    return visitor.leaves
        return [node]

    def recurse_Attribute(self, node: cst.Attribute) -> list[cst.CSTNode]:
        # TODO attributes may have been assigned, should those be modified?
        # research how to detect attribute assigns in libcst
        return [node]

    def _find_gparent(self, n: cst.CSTNode) -> Optional[cst.CSTNode]:
        gparent = None
        try:
            parent = self.get_metadata(ParentNodeProvider, n)
            gparent = self.get_metadata(ParentNodeProvider, parent)
        except Exception:
            pass
        return gparent


class ExtractParameters(ContextAwareVisitor):
    """
    Detects injections and gather the expressions that are injectable.
    """

    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
    )

    quote_pattern = re.compile(r"(?<!\\)\\'|(?<!\\)'")
    raw_quote_pattern = re.compile(r"(?<!\\)'")

    def __init__(self, context: CodemodContext, query: list[cst.CSTNode]) -> None:
        self.query: list[cst.CSTNode] = query
        self.injection_patterns: list[
            Tuple[cst.CSTNode, list[cst.CSTNode], cst.CSTNode]
        ] = []
        super().__init__(context)

    def leave_Module(self, original_node: cst.Module):
        leaves = list(reversed(self.query))
        # treat it as a stack
        modulo_2 = 1
        while leaves:
            # search for the literal start
            start = leaves.pop()
            if not self._is_literal_start(start, modulo_2):
                continue
            middle = []
            # gather expressions until the literal ends
            while leaves and not self._is_literal_end(leaves[-1]):
                middle.append(leaves.pop())
            # could not find the literal end
            if not leaves:
                break
            end = leaves.pop()
            if any(map(self._is_injectable, middle)):
                self.injection_patterns.append((start, middle, end))
            # end may contain the start of another literal, put it back
            # should not be a single quote

            # TODO think of a better solution here
            if self._is_literal_start(end, 0) and self._is_not_a_single_quote(end):
                modulo_2 = 0
                leaves.append(end)
            else:
                modulo_2 = 1

    def _is_not_a_single_quote(self, expression: cst.CSTNode) -> bool:
        match expression:
            case cst.SimpleString():
                prefix = expression.prefix.lower()
                if "b" in prefix:
                    return False
                if "r" in prefix:
                    return (
                        self.raw_quote_pattern.fullmatch(expression.raw_value) is None
                    )
                return self.quote_pattern.fullmatch(expression.raw_value) is None
        return True

    def _is_injectable(self, expression: cst.CSTNode) -> bool:
        # TODO exceptions
        # tuple and list literals ???
        # BinaryExpression case
        match expression:
            case cst.Integer() | cst.Float() | cst.Imaginary() | cst.SimpleString():
                return False
            case cst.Call(func=cst.Name(value="str"), args=[cst.Arg(value=arg), *_]):
                # TODO
                # treat str(encoding = 'utf-8', object=obj)
                # ensure this is the built-in
                if matchers.matches(arg, literal):  # type: ignore
                    return False
            case cst.FormattedStringExpression() if matchers.matches(
                expression, literal
            ):
                return False
            case cst.IfExp():
                return self._is_injectable(expression.body) or self._is_injectable(
                    expression.orelse
                )
        return True

    def _is_literal_start(self, node: cst.CSTNode, modulo_2: int) -> bool:
        # TODO limited for now, won't include cases like "name = 'username_" + name + "_tail'"
        match node:
            case cst.SimpleString():
                prefix = node.prefix.lower()
                if "b" in prefix:
                    return False
                if "r" in prefix:
                    matches = list(self.raw_quote_pattern.finditer(node.raw_value))
                else:
                    matches = list(self.quote_pattern.finditer(node.raw_value))
                # avoid cases like: "where name = 'foo\\\'s name'"
                # don't count \\' as these are escaped in string literals
                return (
                    matches[-1].end() == len(node.raw_value)
                    if matches and len(matches) % 2 == modulo_2
                    else False
                )
            case cst.FormattedStringText():
                # TODO may be in the middle i.e. f"name='home_{exp}'"
                # be careful of f"name='literal'", it needs one but not two
                return False
        return False

    def _is_literal_end(self, node: cst.CSTNode) -> bool:
        match node:
            case cst.SimpleString():
                if "b" in node.prefix:
                    return False
                if "r" in node.prefix:
                    matches = list(self.raw_quote_pattern.finditer(node.raw_value))
                else:
                    matches = list(self.quote_pattern.finditer(node.raw_value))
                return matches[0].start() == 0 if matches else False
            case cst.FormattedStringText():
                # TODO may be in the middle i.e. f"'{exp}_home'"
                # be careful of f"name='literal'", it needs one but not two
                return False
        return False


class FindQueryCalls(ContextAwareVisitor):
    """
    Find all the execute calls with a sql query as an argument.
    """

    # right now it works by looking into some sql keywords in any pieces of the query
    # Ideally we should infer what driver we are using
    sql_keywords: list[str] = ["insert", "select", "delete", "create", "alter", "drop"]

    def __init__(self, context: CodemodContext) -> None:
        self.calls: dict = {}
        super().__init__(context)

    def _has_keyword(self, string: str) -> bool:
        for keyword in self.sql_keywords:
            if keyword in string.lower():
                return True
        return False

    def leave_Call(self, original_node: cst.Call) -> None:
        maybe_call_name = get_function_name_node(original_node)
        if maybe_call_name and maybe_call_name.value == "execute":
            # TODO don't parameterize if there are parameters already
            # may be temporary until I figure out if named parameter will work on most drivers
            if len(original_node.args) > 0 and len(original_node.args) < 2:
                first_arg = original_node.args[0] if original_node.args else None
                if first_arg:
                    query_visitor = LinearizeQuery(self.context)
                    first_arg.value.visit(query_visitor)
                    for expr in query_visitor.leaves:
                        match expr:
                            case cst.SimpleString() | cst.FormattedStringText() if self._has_keyword(
                                expr.value
                            ):
                                self.calls[original_node] = query_visitor.leaves
