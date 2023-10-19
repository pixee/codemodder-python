import re
from typing import Optional, Tuple, Union
import libcst as cst
from libcst import CSTTransformer, SimpleWhitespace, matchers
from libcst.codemod import Codemod, CodemodContext, ContextAwareVisitor
from libcst.metadata import (
    ClassScope,
    GlobalScope,
    ParentNodeProvider,
    PositionProvider,
    ScopeProvider,
)

from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.utils import ReplaceNodes
from codemodder.codemods.utils_mixin import NameResolutionMixin

parameter_token = "?"

literal_number = matchers.Integer() | matchers.Float() | matchers.Imaginary()
literal_string = matchers.SimpleString()
literal = literal_number | literal_string


class SQLQueryParameterization(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Parameterize SQL queries."),
        NAME="sql-parameterization",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        REFERENCES=[],
    )
    SUMMARY = "Parameterize SQL queries."
    CHANGE_DESCRIPTION = ""

    METADATA_DEPENDENCIES = (
        PositionProvider,
        ScopeProvider,
        ParentNodeProvider,
    )
    METADATA_DEPENDENCIES = (
        ScopeProvider,
        ParentNodeProvider,
    )

    def __init__(self, context: CodemodContext, *codemod_args) -> None:
        self.changed_nodes = {}
        self.parameters = []
        Codemod.__init__(self, context)
        BaseCodemod.__init__(self, *codemod_args)

    def _build_param_element(self, middle, index: int):
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

        for call, query in find_queries.calls.items():
            ep = ExtractParameters(self.context, query)
            tree.visit(ep)
            params_elements: list[cst.Element] = []
            for start, middle, end in ep.injection_patterns:
                if len(middle) == 1:
                    element_wrap = cst.Element(
                        value=middle[0],
                        comma=cst.Comma(whitespace_after=SimpleWhitespace(" ")),
                    )
                    params_elements.append(element_wrap)
                else:
                    # TODO support for elements from f-strings?
                    # reminder that python has no implicit conversion while concatenating with +, might need to use str() for a particular expression
                    expr = self._build_param_element(middle, len(middle) - 1)
                    params_elements.append(cst.Element(value=expr, comma=cst.Comma()))
                self._fix_injection(start, middle, end)
            # TODO research if named parameters are widely supported
            # it could solve for the case of existing parameters
            tuple_arg = cst.Arg(cst.Tuple(elements=params_elements))
            self.changed_nodes[call] = call.with_changes(args=[*call.args, tuple_arg])
        if self.changed_nodes:
            result = tree.visit(ReplaceNodes(self.changed_nodes))
            return result.visit(RemoveEmptyStringConcatenation())
        return tree

    def _fix_injection(
        self, start: cst.CSTNode, middle: list[cst.CSTNode], end: cst.CSTNode
    ):
        for expr in middle:
            self.changed_nodes[expr] = cst.parse_expression('""')
        # remove quote literal from end
        match end:
            # TODO test with escaped strings here...
            case cst.SimpleString():
                current_end = self.changed_nodes.get(end) or end
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

    def visit_Attribute(self, node: cst.Attribute) -> Optional[bool]:
        self.leaves.append(node)

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

    def leave_Module(self, tree: cst.Module):
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
            # end may contain the start of anothe literal, put it back
            # should not be a single quote
            # TODO think of a better solution here
            if self._is_not_a_single_quote(end):
                modulo_2 = 0
                leaves.append(end)
            else:
                modulo_2 = 1

            # TODO use changed nodes to detect if start has already been modified before
            # this can happen if start = end of another expression

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
            case cst.Call(func=cst.Name(value="str"), args=[arg, *_]):
                # TODO
                # treat str(encoding = 'utf-8', object=obj)
                # ensure this is the built-in
                if matchers.matches(arg, literal_number):
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
        maybe_call_name = _get_function_name_node(original_node)
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


def _get_function_name_node(call: cst.Call) -> Optional[cst.Name]:
    match call.func:
        case cst.Name():
            return call.func
        case cst.Attribute():
            return call.func.attr
    return None


class RemoveEmptyStringConcatenation(CSTTransformer):
    """
    Removes concatenation with empty strings (e.g. "hello " + "") or "hello" ""
    """

    # TODO What about empty f-strings? they are a different type of node
    # may not be necessary if handled correctly
    def leave_BinaryOperation(
        self, original_node: cst.BinaryOperation, updated_node: cst.BinaryOperation
    ) -> cst.BaseExpression:
        return self.handle_node(updated_node)

    def leave_ConcatenatedString(
        self,
        original_node: cst.ConcatenatedString,
        updated_node: cst.ConcatenatedString,
    ) -> cst.BaseExpression:
        return self.handle_node(updated_node)

    def handle_node(
        self, updated_node: Union[cst.BinaryOperation, cst.ConcatenatedString]
    ) -> cst.BaseExpression:
        match updated_node.left:
            case cst.SimpleString() if updated_node.left.raw_value == "":
                match updated_node.right:
                    case cst.SimpleString() if updated_node.right.raw_value == "":
                        return cst.SimpleString(value='""')
                    case _:
                        return updated_node.right
        match updated_node.right:
            case cst.SimpleString() if updated_node.right.raw_value == "":
                match updated_node.left:
                    case cst.SimpleString() if updated_node.left.raw_value == "":
                        return cst.SimpleString(value='""')
                    case _:
                        return updated_node.left
        return updated_node
