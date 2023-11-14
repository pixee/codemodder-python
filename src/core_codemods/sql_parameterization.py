import re
from typing import Any, Optional, Tuple
import itertools
import libcst as cst
from libcst import (
    FormattedString,
    SimpleString,
    SimpleWhitespace,
    ensure_type,
    matchers,
)
from libcst.codemod import (
    Codemod,
    CodemodContext,
    ContextAwareTransformer,
    ContextAwareVisitor,
)
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
from codemodder.codemods.utils import (
    Append,
    BaseType,
    ReplaceNodes,
    get_function_name_node,
    infer_expression_type,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.file_context import FileContext

parameter_token = "?"

quote_pattern = re.compile(r"(?<!\\)\\'|(?<!\\)'")
raw_quote_pattern = re.compile(r"(?<!\\)'")


class SQLQueryParameterization(BaseCodemod, UtilsMixin, Codemod):
    SUMMARY = "Parameterize SQL Queries"
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
        file_context: FileContext,
        *codemod_args,
    ) -> None:
        self.changed_nodes: dict[
            cst.CSTNode,
            cst.CSTNode | cst.RemovalSentinel | cst.FlattenSentinel | dict[str, Any],
        ] = {}
        BaseCodemod.__init__(self, file_context, *codemod_args)
        UtilsMixin.__init__(self, [])
        Codemod.__init__(self, context)

    def _build_param_element(self, prepend, middle, append):
        new_middle = (
            ([prepend] if prepend else []) + middle + ([append] if append else [])
        )
        format_pieces: list[str] = []
        format_expr_count = 0
        args = []
        if len(new_middle) == 1:
            # TODO maybe handle conversion here?
            return new_middle[0]
        for e in new_middle:
            exception = False
            if isinstance(e, cst.SimpleString | cst.FormattedStringText):
                t = _extract_prefix_raw_value(self, e)
                if t:
                    prefix, raw_value = t
                    if not "b" in prefix and not "r" in prefix and not "u" in prefix:
                        format_pieces.append(raw_value)
                        exception = True
            if not exception:
                format_pieces.append(f"{{{format_expr_count}}}")
                format_expr_count += 1
                args.append(cst.Arg(e))

        format_string = "".join(format_pieces)
        format_string_node = cst.SimpleString(f"'{format_string}'")
        return cst.Call(
            func=cst.Attribute(value=format_string_node, attr=cst.Name(value="format")),
            args=args,
        )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        # The transformation has four major steps:
        # (1) FindQueryCalls - Find and gather all the SQL query execution calls. The result is a dict of call nodes and their associated list of nodes composing the query (i.e. step (2)).
        # (2) LinearizeQuery - For each call, it gather all the string literals and expressions that composes the query. The result is a list of nodes whose concatenation is the query.
        # (3) ExtractParameters - Detects which expressions are part of SQL string literals in the query. The result is a list of triples (a,b,c) such that a is the node that contains the start of the string literal, b is a list of expressions that composes that literal, and c is the node containing the end of the string literal. At least one node in b must be "injectable" (see).
        # (4) SQLQueryParameterization - Executes steps (1)-(3) and gather a list of injection triples. For each triple (a,b,c) it makes the associated changes to insert the query parameter token. All the expressions in b are then concatenated in an expression and passed as a sequence of parameters to the execute call.

        # Steps (1) and (2)
        find_queries = FindQueryCalls(self.context)
        tree.visit(find_queries)

        result = tree
        for call, query in find_queries.calls.items():
            # filter by line includes/excludes
            call_pos = self.node_position(call)
            if not self.filter_by_path_includes_or_excludes(call_pos):
                break

            # Step (3)
            ep = ExtractParameters(self.context, query)
            tree.visit(ep)

            # Step (4) - build tuple elements and fix injection
            params_elements: list[cst.Element] = []
            for start, middle, end in ep.injection_patterns:
                prepend, append = self._fix_injection(start, middle, end)
                expr = self._build_param_element(prepend, middle, append)
                params_elements.append(
                    cst.Element(
                        value=expr,
                        comma=cst.Comma(whitespace_after=SimpleWhitespace(" ")),
                    )
                )

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
                    Change(line_number, SQLQueryParameterization.CHANGE_DESCRIPTION)
                )
                # Normalization and cleanup
                result = result.visit(RemoveEmptyStringConcatenation())
                result = NormalizeFStrings(self.context).transform_module(result)
                # TODO The transform below may break nested f-strings: f"{f"1"}" -> f"{"1"}"
                # May be a bug...
                # result = UnnecessaryFormatString(self.context).transform_module(result)

        return result

    def _fix_injection(
        self, start: cst.CSTNode, middle: list[cst.CSTNode], end: cst.CSTNode
    ):
        for expr in middle:
            if isinstance(
                expr, cst.FormattedStringText | cst.FormattedStringExpression
            ):
                self.changed_nodes[expr] = cst.RemovalSentinel.REMOVE
            else:
                self.changed_nodes[expr] = cst.parse_expression('""')

        # remove quote literal from start
        updated_start = self.changed_nodes.get(start) or start

        t = _extract_prefix_raw_value(self, updated_start)
        prefix, raw_value = t if t else ("", "")

        # gather string after the quote
        if "r" in prefix:
            quote_span = list(raw_quote_pattern.finditer(raw_value))[-1]
        else:
            quote_span = list(quote_pattern.finditer(raw_value))[-1]

        new_raw_value = raw_value[: quote_span.start()] + parameter_token
        prepend_raw_value = raw_value[quote_span.end() :]

        prepend = self._remove_literal_and_gather_extra(
            start, updated_start, prefix, new_raw_value, prepend_raw_value
        )

        # remove quote literal from end
        updated_end = self.changed_nodes.get(end) or end

        t = _extract_prefix_raw_value(self, updated_end)
        prefix, raw_value = t if t else ("", "")
        if "r" in prefix:
            quote_span = list(raw_quote_pattern.finditer(raw_value))[0]
        else:
            quote_span = list(quote_pattern.finditer(raw_value))[0]

        new_raw_value = raw_value[quote_span.end() :]
        append_raw_value = raw_value[: quote_span.start()]

        append = self._remove_literal_and_gather_extra(
            end, updated_end, prefix, new_raw_value, append_raw_value
        )

        return (prepend, append)

    # pylint: disable-next=too-many-arguments
    def _remove_literal_and_gather_extra(
        self, original_node, updated_node, prefix, new_raw_value, extra_raw_value
    ) -> Optional[SimpleString]:
        extra = None
        match updated_node:
            case cst.SimpleString():
                # gather string after or before the quote
                if extra_raw_value:
                    extra = cst.SimpleString(
                        value=updated_node.prefix
                        + updated_node.quote
                        + extra_raw_value
                        + updated_node.quote
                    )

                new_value = (
                    updated_node.prefix
                    + updated_node.quote
                    + new_raw_value
                    + updated_node.quote
                )
                self.changed_nodes[original_node] = updated_node.with_changes(
                    value=new_value
                )
            case cst.FormattedStringText():
                if extra_raw_value:
                    extra = cst.SimpleString(
                        value=("r" if "r" in prefix else "")
                        + "'"
                        + extra_raw_value
                        + "'"
                    )

                new_value = new_raw_value
                self.changed_nodes[original_node] = updated_node.with_changes(
                    value=new_value
                )
        return extra


class LinearizeQuery(ContextAwareVisitor, NameResolutionMixin):
    """
    Gather all the expressions that are concatenated to build the query.
    """

    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, context) -> None:
        super().__init__(context)
        self.leaves: list[cst.CSTNode] = []

    def on_visit(self, node: cst.CSTNode):
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
                | matchers.FormattedString()
                | matchers.BinaryOperation()
                | matchers.FormattedStringExpression()
                | matchers.ConcatenatedString(),
            ):
                self.leaves.append(node)
            else:
                return super().on_visit(node)
        return False

    def visit_BinaryOperation(self, node: cst.BinaryOperation) -> Optional[bool]:
        maybe_type = infer_expression_type(node)
        if not maybe_type or maybe_type == BaseType.STRING:
            return True
        self.leaves.append(node)
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

    def __init__(self, context: CodemodContext, query: list[cst.CSTNode]) -> None:
        self.query: list[cst.CSTNode] = query
        self.injection_patterns: list[
            Tuple[cst.CSTNode, list[cst.CSTNode], cst.CSTNode]
        ] = []
        super().__init__(context)

    def leave_Module(self, original_node: cst.Module):
        leaves = list(reversed(self.query))
        modulo_2 = 1
        # treat it as a stack
        while leaves:
            # search for the literal start, we detect the single quote
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

            if self._is_literal_start(end, 0) and self._is_not_a_single_quote(end):
                modulo_2 = 0
                leaves.append(end)
            else:
                modulo_2 = 1

    def _is_not_a_single_quote(self, expression: cst.CSTNode) -> bool:
        t = _extract_prefix_raw_value(self, expression)
        if not t:
            return True
        prefix, raw_value = t
        if "b" in prefix:
            return False
        if "r" in prefix:
            return raw_quote_pattern.fullmatch(raw_value) is None
        return quote_pattern.fullmatch(raw_value) is None

    def _is_injectable(self, expression: cst.BaseExpression) -> bool:
        return not bool(infer_expression_type(expression))

    def _is_literal_start(self, node: cst.CSTNode, modulo_2: int) -> bool:
        t = _extract_prefix_raw_value(self, node)
        if not t:
            return False
        prefix, raw_value = t
        if "b" in prefix:
            return False
        if "r" in prefix:
            matches = list(raw_quote_pattern.finditer(raw_value))
        else:
            matches = list(quote_pattern.finditer(raw_value))
        # avoid cases like: "where name = 'foo\\\'s name'"
        # don't count \\' as these are escaped in string literals
        return (matches != None) and len(matches) % 2 == modulo_2

    def _is_literal_end(self, node: cst.CSTNode) -> bool:
        t = _extract_prefix_raw_value(self, node)
        if not t:
            return False
        prefix, raw_value = t
        if "b" in prefix:
            return False
        if "r" in prefix:
            matches = list(raw_quote_pattern.finditer(raw_value))
        else:
            matches = list(quote_pattern.finditer(raw_value))
        return bool(matches)


class NormalizeFStrings(ContextAwareTransformer):
    """
    Finds all the f-strings whose parts are only composed of FormattedStringText and concats all of them in a single part.
    """

    def leave_FormattedString(
        self, original_node: cst.FormattedString, updated_node: cst.FormattedString
    ) -> cst.BaseExpression:
        all_parts = list(
            itertools.takewhile(
                lambda x: isinstance(x, cst.FormattedStringText), original_node.parts
            )
        )
        if len(all_parts) != len(updated_node.parts):
            return updated_node
        new_part = cst.FormattedStringText(
            value="".join(map(lambda x: x.value, all_parts))
        )
        return updated_node.with_changes(parts=[new_part])


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


def _extract_prefix_raw_value(self, node) -> Optional[Tuple[str, str]]:
    match node:
        case cst.SimpleString():
            return node.prefix.lower(), node.raw_value
        case cst.FormattedStringText():
            try:
                parent = self.get_metadata(ParentNodeProvider, node)
                parent = ensure_type(parent, FormattedString)
            except Exception:
                return None
            return parent.start.lower(), node.value
        case _:
            return None
