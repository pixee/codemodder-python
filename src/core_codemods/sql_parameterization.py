import itertools
import re
from dataclasses import replace
from typing import Any, Optional, Tuple

import libcst as cst
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

from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.transformations.remove_empty_string_concatenation import (
    RemoveEmptyStringConcatenation,
)
from codemodder.codemods.utils import (
    Append,
    ReplacementNodeType,
    ReplaceNodes,
    get_function_name_node,
    infer_expression_type,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.codetf import Change
from codemodder.utils.format_string_parser import (
    FormattedLiteralStringExpression,
    FormattedLiteralStringText,
    dict_to_values_dict,
    expressions_from_replacements,
    parse_formatted_string,
)
from codemodder.utils.linearize_string_expression import (
    LinearizedStringExpression,
    LinearizeStringMixin,
)
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod

parameter_token = "?"

quote_pattern = re.compile(r"(?<!\\)\\'|(?<!\\)'")
raw_quote_pattern = re.compile(r"(?<!\\)'")


class SQLQueryParameterizationTransformer(LibcstResultTransformer, UtilsMixin):
    change_description = "Parameterized SQL query execution."

    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        ParentNodeProvider,
    )

    def __init__(
        self,
        *codemod_args,
        **codemod_kwargs,
    ) -> None:
        self.changed_nodes: dict[
            cst.CSTNode,
            ReplacementNodeType | dict[str, Any],
        ] = {}
        LibcstResultTransformer.__init__(self, *codemod_args, **codemod_kwargs)
        UtilsMixin.__init__(
            self,
            [],
            line_exclude=self.file_context.line_exclude,
            line_include=self.file_context.line_include,
        )

    def _build_param_element(self, prepend, middle, append, linearized_query):
        middle = [linearized_query.aliased.get(e, e) for e in middle]
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
            if isinstance(
                e,
                cst.SimpleString | cst.FormattedStringText | FormattedLiteralStringText,
            ):
                t = _extract_prefix_raw_value(self, e)
                if t:
                    prefix, raw_value = t
                    if all(char not in prefix for char in "bru"):
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
        for call, linearized_query in find_queries.calls.items():
            # filter by line includes/excludes
            call_pos = self.node_position(call)
            if not self.filter_by_path_includes_or_excludes(call_pos):
                break

            # Step (3)
            ep = ExtractParameters(self.context, linearized_query)
            tree.visit(ep)

            # Step (4) - build tuple elements and fix injection
            params_elements: list[cst.Element] = []
            for start, middle, end in ep.injection_patterns:
                prepend, append = self._fix_injection(
                    start, middle, end, linearized_query
                )
                expr = self._build_param_element(
                    prepend, middle, append, linearized_query
                )
                params_elements.append(
                    cst.Element(
                        value=expr,
                        comma=cst.Comma(whitespace_after=cst.SimpleWhitespace(" ")),
                    )
                )

            # TODO research if named parameters are widely supported
            # it could solve for the case of existing parameters
            # TODO Do all middle expressions hail from a single source?
            # e.g. the following
            # name = 'user_' + input() + '_name'
            # execute("'" + name + "'")
            # should produce: execute("?", name)
            # instead of: execute("?", 'user_{0}_name'.format(input()))
            if params_elements:
                tuple_arg = cst.Arg(cst.Tuple(elements=params_elements))
                # self.changed_nodes[call] = call.with_changes(args=[*call.args, tuple_arg])
                self.changed_nodes[call] = {"args": Append([tuple_arg])}

            # made changes
            if self.changed_nodes:
                # build changed_nodes from parts here
                new_changed_nodes = {}
                new_parts_for = set()
                for k, v in self.changed_nodes.items():
                    match k:
                        case FormattedLiteralStringText():
                            new_parts_for.add(k.origin)
                        case _:
                            new_changed_nodes[k] = v
                for node in new_parts_for:
                    new_raw_value = ""
                    for part in linearized_query.node_pieces[node]:
                        new_part = self.changed_nodes.get(part) or part
                        match new_part:
                            case cst.SimpleString():
                                new_raw_value += new_part.raw_value
                            case (
                                FormattedLiteralStringText()
                                | FormattedLiteralStringExpression()
                            ):
                                new_raw_value += new_part.value
                            case _:
                                new_raw_value = ""
                    match node:
                        case cst.SimpleString():
                            new_changed_nodes[node] = node.with_changes(
                                value=node.prefix
                                + node.quote
                                + new_raw_value
                                + node.quote
                            )
                        case cst.FormattedStringText():
                            new_changed_nodes[node] = node.with_changes(
                                value=new_raw_value
                            )

                result = result.visit(ReplaceNodes(new_changed_nodes))
                self.changed_nodes = {}
                line_number = self.get_metadata(PositionProvider, call).start.line
                self.file_context.codemod_changes.append(
                    Change(
                        lineNumber=line_number,
                        description=SQLQueryParameterizationTransformer.change_description,
                    )
                )
                # Normalization and cleanup
                result = RemoveEmptyExpressionsFormatting(
                    self.context
                ).transform_module(result)
                result = result.visit(RemoveEmptyStringConcatenation())
                result = NormalizeFStrings(self.context).transform_module(result)
                # TODO The transform below may break nested f-strings: f"{f"1"}" -> f"{"1"}"
                # May be a bug...
                # result = UnnecessaryFormatString(self.context).transform_module(result)

        return result

    def _fix_injection(
        self,
        start: cst.CSTNode,
        middle: list[cst.CSTNode],
        end: cst.CSTNode,
        linearized_query: LinearizedStringExpression,
    ):
        for expr in middle:
            if expr in linearized_query.aliased:
                self.changed_nodes[linearized_query.aliased[expr]] = (
                    cst.parse_expression('""')
                )
            else:
                match expr:
                    case cst.FormattedStringText() | cst.FormattedStringExpression():
                        self.changed_nodes[expr] = cst.RemovalSentinel.REMOVE
                    case _:
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

    def _remove_literal_and_gather_extra(
        self, original_node, updated_node, prefix, new_raw_value, extra_raw_value
    ) -> Optional[cst.SimpleString]:
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
            case FormattedLiteralStringText():
                if extra_raw_value:
                    extra = cst.SimpleString(
                        value=("r" if "r" in prefix else "")
                        + "'"
                        + extra_raw_value
                        + "'"
                    )

                new_value = new_raw_value
                self.changed_nodes[original_node] = replace(
                    updated_node, value=new_value
                )
        return extra


SQLQueryParameterization = CoreCodemod(
    metadata=Metadata(
        name="sql-parameterization",
        summary="Parameterize SQL Queries",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(url="https://cwe.mitre.org/data/definitions/89.html"),
            Reference(url="https://owasp.org/www-community/attacks/SQL_Injection"),
        ],
    ),
    transformer=LibcstTransformerPipeline(SQLQueryParameterizationTransformer),
    detector=None,
)


class ExtractParameters(ContextAwareVisitor, NameAndAncestorResolutionMixin):
    """
    Detects injections and gather the expressions that are injectable.
    """

    def __init__(
        self,
        context: CodemodContext,
        linearized_query: LinearizedStringExpression,
    ) -> None:
        self.linearized_query = linearized_query
        self.injection_patterns: list[
            tuple[
                cst.CSTNode,
                list[cst.CSTNode],
                cst.CSTNode,
            ]
        ] = []
        super().__init__(context)

    def leave_Module(self, original_node: cst.Module):
        leaves = list(reversed(self.linearized_query.parts))
        modulo_2 = 1
        # treat it as a stack
        while leaves:
            # TODO check if we can change values here any expression in middle should not be from GlobalScope or ClassScope
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
                if (
                    self._can_be_changed(start)
                    and self._can_be_changed(end)
                    and all(map(self._can_be_changed_middle, middle))
                ):
                    self.injection_patterns.append((start, middle, end))
            # end may contain the start of another literal, put it back
            # should not be a single quote

            if self._is_literal_start(end, 0) and self._is_not_a_single_quote(end):
                modulo_2 = 0
                leaves.append(end)
            else:
                modulo_2 = 1

    def _is_not_a_single_quote(self, expression: cst.CSTNode) -> bool:
        value = expression
        t = _extract_prefix_raw_value(self, value)
        if not t:
            return True
        prefix, raw_value = t
        if "b" in prefix:
            return False
        if "r" in prefix:
            return raw_quote_pattern.fullmatch(raw_value) is None
        return quote_pattern.fullmatch(raw_value) is None

    def _is_assigned_to_exposed_scope(self, expression):
        named, other = self.find_transitive_assignment_targets(expression)
        for t in itertools.chain(named, other):
            scope = self.get_metadata(ScopeProvider, t, None)
            match scope:
                case GlobalScope() | ClassScope() | None:
                    return True
        return False

    def _is_target_in_expose_scope(self, expression):
        assignments = self.find_assignments(expression)
        for assignment in assignments:
            match assignment.scope:
                case GlobalScope() | ClassScope() | None:
                    return True
        return False

    def _can_be_changed_middle(self, expression):
        # is it assigned to a variable with global/class scope?
        # is itself a target in global/class scope?
        # if the expression is aliased, it is just a reference and we can always change
        match expression:
            case FormattedLiteralStringText():
                expression = expression.origin

        if expression in self.linearized_query.aliased:
            return True
        return not (
            self._is_target_in_expose_scope(expression)
            or self._is_assigned_to_exposed_scope(expression)
        )

    def _can_be_changed(self, expression):
        # is it assigned to a variable with global/class scope?
        # is itself a target in global/class scope?
        match expression:
            case FormattedLiteralStringText():
                expression = expression.origin
        return not (
            self._is_target_in_expose_scope(expression)
            or self._is_assigned_to_exposed_scope(expression)
        )

    def _is_injectable(self, expression: cst.BaseExpression) -> bool:
        return not bool(infer_expression_type(expression))

    def _is_literal_start(
        self, node: cst.CSTNode | tuple[cst.CSTNode, cst.CSTNode], modulo_2: int
    ) -> bool:
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
        return (matches is not None) and len(matches) % 2 == modulo_2

    def _is_literal_end(
        self, node: cst.CSTNode | tuple[cst.CSTNode, cst.CSTNode]
    ) -> bool:
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


class FindQueryCalls(ContextAwareVisitor, LinearizeStringMixin):
    """
    Find all the execute calls with a sql query as an argument.
    """

    # Right now it works by looking into some sql keywords in any pieces of the query
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
                    linearized_string_expr = self.linearize_string_expression(
                        first_arg.value
                    )
                    for part in (
                        linearized_string_expr.parts if linearized_string_expr else []
                    ):
                        match part:
                            case (
                                cst.SimpleString()
                                | cst.FormattedStringText()
                                | FormattedLiteralStringText()
                            ) if self._has_keyword(part.value):
                                self.calls[original_node] = linearized_string_expr
                                break


def _extract_prefix_raw_value(self, node) -> Optional[Tuple[str, str]]:
    match node:
        case cst.SimpleString():
            return node.prefix.lower(), node.raw_value
        case cst.FormattedStringText():
            try:
                parent = self.get_metadata(ParentNodeProvider, node)
                parent = cst.ensure_type(parent, cst.FormattedString)
            except Exception:
                return None
            return parent.start.lower(), node.value
        case FormattedLiteralStringText():
            maybe_t = _extract_prefix_raw_value(self, node.origin)
            if maybe_t:
                prefix, _ = maybe_t
                return prefix, node.value
            return None
        case _:
            return None


class RemoveEmptyExpressionsFormatting(Codemod):

    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        ScopeProvider,
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        result = tree
        visitor = RemoveEmptyExpressionsFormattingVisitor(self.context)
        result.visit(visitor)
        if visitor.node_replacements:
            result = result.visit(ReplaceNodes(visitor.node_replacements))
        return result

    def should_allow_multiple_passes(self) -> bool:
        return True


class RemoveEmptyExpressionsFormattingVisitor(
    ContextAwareVisitor, NameAndAncestorResolutionMixin, LinearizeStringMixin
):

    def __init__(self, context: CodemodContext) -> None:
        self.node_replacements: dict[cst.CSTNode, ReplacementNodeType] = {}
        super().__init__(context)

    def _resolve_dict(
        self, dict_node: cst.Dict
    ) -> dict[cst.BaseExpression, cst.BaseExpression]:
        returned: dict[cst.BaseExpression, cst.BaseExpression] = {}
        for element in dict_node.elements:
            match element:
                case cst.DictElement():
                    returned |= {element.key: element.value}
                case cst.StarredDictElement():
                    resolved = self.resolve_expression(element.value)
                    if isinstance(resolved, cst.Dict):
                        returned |= self._resolve_dict(resolved)
        return returned

    def _is_empty_sequence_literal(self, expr: cst.BaseExpression) -> bool:
        match expr:
            case cst.Dict() | cst.Tuple() if not expr.elements:
                return True
        return False

    def _build_replacements(self, node, node_parts, parts_to_remove):
        new_raw_value = ""
        change = False
        for part in node_parts:
            if part in parts_to_remove:
                change = True
            else:
                new_raw_value += part.value
        if change:
            match node:
                case cst.SimpleString():
                    self.node_replacements[node] = node.with_changes(
                        value=node.prefix + node.quote + new_raw_value + node.quote
                    )
                case cst.FormattedStringText():
                    self.node_replacements[node] = node.with_changes(
                        value=new_raw_value
                    )

    def _record_node_pieces(self, parts) -> dict:
        node_pieces: dict[
            cst.CSTNode,
            list[FormattedLiteralStringExpression | FormattedLiteralStringText],
        ] = {}
        for part in parts:
            match part:
                case FormattedLiteralStringText() | FormattedLiteralStringExpression():
                    if part.origin in node_pieces:
                        node_pieces[part.origin].append(part)
                    else:
                        node_pieces[part.origin] = [part]
        return node_pieces

    def leave_BinaryOperation(self, original_node: cst.BinaryOperation):
        if not isinstance(original_node.operator, cst.Modulo):
            return

        # is left or right an empty literal?
        if _is_empty_string_literal(self.resolve_expression(original_node.left)):
            self.node_replacements[original_node] = cst.SimpleString("''")
            return
        right = self.resolve_expression(right := original_node.right)
        if self._is_empty_sequence_literal(right):
            self.node_replacements[original_node] = original_node.left
            return

        # gather all the parts of the format operator
        match right:
            case cst.Dict():
                resolved_dict = self._resolve_dict(right)
                keys: dict | list = dict_to_values_dict(resolved_dict)
            case _:
                keys = expressions_from_replacements(right)
        linearized_string_expr = self.linearize_string_expression(original_node.left)
        parsed = parse_formatted_string(
            linearized_string_expr.parts if linearized_string_expr else [], keys
        )
        node_pieces = self._record_node_pieces(parsed)

        # failed parsing of expression, aborting
        if not parsed:
            return

        # is there any expressions to replace? if not, remove the operator
        if all(not isinstance(p, FormattedLiteralStringExpression) for p in parsed):
            self.node_replacements[original_node] = original_node.left
            return

        # gather all the expressions parts that resolves to an empty string and remove them
        to_remove = set()
        for part in parsed:
            match part:
                case FormattedLiteralStringExpression():
                    resolved_part_expression = self.resolve_expression(part.expression)
                    if _is_empty_string_literal(resolved_part_expression):
                        to_remove.add(part)
        keys_to_remove = {part.key or 0 for part in to_remove}
        for part in to_remove:
            self._build_replacements(part.origin, node_pieces[part.origin], to_remove)

        # remove all the elements on the right that resolves to an empty string
        match right:
            case cst.Dict():
                for k, v in resolved_dict.items():
                    resolved_v = self.resolve_expression(v)
                    if _is_empty_string_literal(resolved_v):
                        parent = self.get_parent(v)
                        self.node_replacements[parent] = cst.RemovalSentinel.REMOVE

            case cst.Tuple():
                new_tuple_elements = []
                # outright remove
                if len(keys_to_remove) != len(keys):
                    for i, element in enumerate(right.elements):
                        if i not in keys_to_remove:
                            new_tuple_elements.append(element)
                if len(new_tuple_elements) != len(right.elements):
                    if len(new_tuple_elements) == 1:
                        self.node_replacements[right] = new_tuple_elements[0].value
                    else:
                        self.node_replacements[right] = right.with_changes(
                            elements=new_tuple_elements
                        )
            case _:
                if keys_to_remove:
                    self.node_replacements[original_node] = cst.SimpleString("''")


def _is_empty_string_literal(node) -> bool:
    match node:
        case cst.SimpleString() if node.raw_value == "":
            return True
        case cst.FormattedString() if not node.parts:
            return True
    return False
