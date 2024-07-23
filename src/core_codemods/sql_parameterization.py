import itertools
import re
from dataclasses import replace
from typing import Any, ClassVar, Collection, Optional

import libcst as cst
from libcst.codemod import Codemod, CodemodContext, ContextAwareVisitor
from libcst.codemod.commands.unnecessary_format_string import UnnecessaryFormatString
from libcst.metadata import (
    ClassScope,
    GlobalScope,
    ParentNodeProvider,
    PositionProvider,
    ProviderT,
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
from codemodder.utils.clean_code import (
    NormalizeFStrings,
    RemoveEmptyExpressionsFormatting,
    RemoveUnusedVariables,
)
from codemodder.utils.format_string_parser import (
    PrintfStringExpression,
    PrintfStringText,
    StringLiteralNodeType,
    extract_raw_value,
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


class ExtractPrefixMixin(cst.MetadataDependent):

    METADATA_DEPENDENCIES: ClassVar[Collection[ProviderT]] = (ParentNodeProvider,)

    def extract_prefix(self, node: StringLiteralNodeType) -> str:
        match node:
            case cst.SimpleString():
                return node.prefix.lower()
            case cst.FormattedStringText():
                try:
                    parent = self.get_metadata(ParentNodeProvider, node)
                    parent = cst.ensure_type(parent, cst.FormattedString)
                except Exception:
                    return ""
                return parent.start.lower()
            case PrintfStringText():
                return self.extract_prefix(node.origin)
        return ""

    def _extract_prefix_raw_value(self, node: StringLiteralNodeType) -> tuple[str, str]:
        raw_value = extract_raw_value(node)
        prefix = self.extract_prefix(node)
        return prefix, raw_value


class CleanCode(Codemod):

    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        ScopeProvider,
    )

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        result = RemoveEmptyStringConcatenation(self.context).transform_module(tree)
        result = RemoveEmptyExpressionsFormatting(self.context).transform_module(result)
        result = NormalizeFStrings(self.context).transform_module(result)
        result = RemoveUnusedVariables(self.context).transform_module(result)
        result = UnnecessaryFormatString(self.context).transform_module(result)
        return result

    def should_allow_multiple_passes(self) -> bool:
        return True


class SQLQueryParameterizationTransformer(
    LibcstResultTransformer, UtilsMixin, ExtractPrefixMixin
):
    change_description = "Parameterized SQL query execution."

    METADATA_DEPENDENCIES: ClassVar[Collection[ProviderT]] = (
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
            cst.CSTNode | PrintfStringText | PrintfStringExpression,
            ReplacementNodeType
            | PrintfStringText
            | PrintfStringExpression
            | dict[str, Any],
        ] = {}
        LibcstResultTransformer.__init__(self, *codemod_args, **codemod_kwargs)
        UtilsMixin.__init__(
            self,
            codemod_args[1],
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
                e, cst.SimpleString | cst.FormattedStringText | PrintfStringText
            ):
                prefix, raw_value = self._extract_prefix_raw_value(e)
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
        """
        The transformation is composed of 3 steps, each step is done by a codemod/visitor: (1) FindQueryCalls, (2) ExtractParameters, and (3) _fix_injection
        Step (1) finds the `execute` calls and linearizing the query argument. Step (2) extracts the expressions that are parameters to the query.
        Step (3) swaps the parameters in the query for `?` tokens and passes them as an arguments for the `execute` call. At the end of the transformation, the `CleanCode` codemod is executed to remove leftover empty strings and unused variables.
        """

        # Step (1)
        find_queries = FindQueryCalls(self.context)
        tree.visit(find_queries)

        for call, linearized_query in find_queries.calls.items():
            # filter node
            if not self.node_is_selected(call):
                continue

            # Step (2)
            ep = ExtractParameters(self.context, linearized_query)
            tree.visit(ep)

            # Step (3)
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
                self.changed_nodes[call] = {"args": Append([tuple_arg])}

            # made changes
            if self.changed_nodes:
                # build changed_nodes from parts here
                new_changed_nodes = {}
                new_parts_for = set()
                for k, v in self.changed_nodes.items():
                    match k:
                        case PrintfStringText():
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
                            case PrintfStringText() | PrintfStringExpression():
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

                result = tree.visit(ReplaceNodes(new_changed_nodes))
                self.changed_nodes = {}
                line_number = self.get_metadata(PositionProvider, call).start.line
                self.file_context.codemod_changes.append(
                    Change(
                        lineNumber=line_number,
                        description=SQLQueryParameterizationTransformer.change_description,
                        findings=self.file_context.get_findings_for_location(
                            line_number
                        ),
                    )
                )
                # Normalization and cleanup
                result = CleanCode(self.context).transform_module(result)

                # return after a single change
                return result
        return tree

    def should_allow_multiple_passes(self) -> bool:
        return True

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

        prefix, raw_value = self._extract_prefix_raw_value(updated_start)

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

        prefix, raw_value = self._extract_prefix_raw_value(updated_end)
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
                        value=("r" if "r" in prefix else "") + f"'{extra_raw_value}'"
                    )

                new_value = new_raw_value
                self.changed_nodes[original_node] = updated_node.with_changes(
                    value=new_value
                )
            case PrintfStringText():
                if extra_raw_value:
                    extra = cst.SimpleString(
                        value=("r" if "r" in prefix else "") + f"'{extra_raw_value}'"
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


class ExtractParameters(
    ContextAwareVisitor, NameAndAncestorResolutionMixin, ExtractPrefixMixin
):
    """
    This visitor a takes the linearized query and extracts the expressions that are parameters in this query. An expression is a parameter if it is surrounded by single quotes in the query. It results in a list of triples (start, middle, end), where start and end contains the expressions with single quotes marking the parameter, and middle is a list of expressions that composes the parameter.
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

    def _is_not_a_single_quote(self, expression: StringLiteralNodeType) -> bool:
        prefix, raw_value = self._extract_prefix_raw_value(expression)
        if "b" in prefix:
            return False
        if "r" in prefix:
            return raw_quote_pattern.fullmatch(raw_value) is None
        return quote_pattern.fullmatch(raw_value) is None

    def _is_assigned_to_exposed_scope(self, expression):
        # is it part of an expression that is assigned to a variable in an exposed scope?
        path = self.path_to_root(expression)
        for i, node in enumerate(path):
            # ensure it descend from the value attribute
            if isinstance(node, cst.Assign) and (i > 0 and path[i - 1] == node.value):
                expression = node.value
                scope = self.get_metadata(ScopeProvider, node, None)
                match scope:
                    case GlobalScope() | ClassScope() | None:
                        return True

        named, other = self.find_transitive_assignment_targets(expression)
        for t in itertools.chain(named, other):
            scope = self.get_metadata(ScopeProvider, t, None)
            match scope:
                case GlobalScope() | ClassScope() | None:
                    return True
        return False

    def _is_target_in_exposed_scope(self, expression):
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
            case PrintfStringText():
                expression = expression.origin

        if expression in self.linearized_query.aliased:
            return True
        return not (
            self._is_target_in_exposed_scope(expression)
            or self._is_assigned_to_exposed_scope(expression)
        )

    def _can_be_changed(self, expression):
        # is it assigned to a variable with global/class scope?
        # is itself a target in global/class scope?
        match expression:
            case PrintfStringText():
                expression = expression.origin
        return not (
            self._is_target_in_exposed_scope(expression)
            or self._is_assigned_to_exposed_scope(expression)
        )

    def _is_injectable(self, expression: cst.BaseExpression) -> bool:
        return not bool(infer_expression_type(expression))

    def _is_literal_start(
        self,
        node: cst.CSTNode | PrintfStringText | PrintfStringExpression,
        modulo_2: int,
    ) -> bool:
        if isinstance(
            node, cst.SimpleString | cst.FormattedStringText | PrintfStringText
        ):
            prefix, raw_value = self._extract_prefix_raw_value(node)

            if "b" in prefix:
                return False
            if "r" in prefix:
                matches = list(raw_quote_pattern.finditer(raw_value))
            else:
                matches = list(quote_pattern.finditer(raw_value))
            # avoid cases like: "where name = 'foo\\\'s name'"
            # don't count \\' as these are escaped in string literals
            return (matches is not None) and len(matches) % 2 == modulo_2
        return False

    def _is_literal_end(
        self, node: cst.CSTNode | PrintfStringExpression | PrintfStringText
    ) -> bool:
        if isinstance(
            node, cst.SimpleString | cst.FormattedStringText | PrintfStringText
        ):
            prefix, raw_value = self._extract_prefix_raw_value(node)
            if prefix is None:
                return False

            if "b" in prefix:
                return False
            if "r" in prefix:
                matches = list(raw_quote_pattern.finditer(raw_value))
            else:
                matches = list(quote_pattern.finditer(raw_value))
            return bool(matches)
        return False


class FindQueryCalls(ContextAwareVisitor, LinearizeStringMixin):
    """
    Finds `execute` calls and linearizes the query argument. The result is a dict mappig each detected call with the linearized query.
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
                                | PrintfStringText()
                            ) if self._has_keyword(part.value):
                                self.calls[original_node] = linearized_string_expr
                                break
