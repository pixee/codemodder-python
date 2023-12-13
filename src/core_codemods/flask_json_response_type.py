from typing import Optional, Tuple
import libcst as cst
from libcst.codemod import CodemodContext, ContextAwareVisitor
from codemodder.codemods.api import BaseCodemod

from codemodder.codemods.base_codemod import ReviewGuidance

from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin


class FlaskJsonResponseType(BaseCodemod, NameAndAncestorResolutionMixin):
    NAME = "flask-json-response-type"
    SUMMARY = "Set content type to `application/json` for `flask.make_response` with JSON data"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Sets `mimetype` to `application/json`."
    REFERENCES = [
        {
            "url": "https://flask.palletsprojects.com/en/2.3.x/patterns/javascript/#return-json-from-views",
            "description": "",
        },
        {
            "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#output-encoding-for-javascript-contexts",
            "description": "",
        },
    ]

    content_type_key = "Content-Type"
    json_content_type = "application/json"

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        visitor = FlaskJsonResponseTypeVisitor(self.context)
        tree.visit(visitor)
        if visitor.node_and_replacement:
            node, replacement = visitor.node_and_replacement
            self.report_change(node)
            return tree.deep_replace(node, replacement)
        return tree


class FlaskJsonResponseTypeVisitor(ContextAwareVisitor, NameAndAncestorResolutionMixin):
    content_type_key = "Content-Type"
    json_content_type = "application/json"

    def __init__(self, context: CodemodContext) -> None:
        self.node_and_replacement: Optional[Tuple[cst.CSTNode, cst.CSTNode]] = None
        super().__init__(context)

    def leave_Return(self, original_node: cst.Return):
        if original_node.value:
            # is inside a function def with a route decorator
            maybe_function_def = self.find_immediate_function_def(original_node)
            maybe_has_decorator = (
                self._has_route_decorator(maybe_function_def)
                if maybe_function_def
                else None
            )
            if maybe_has_decorator:
                # json.dumps(...)
                if self._is_json_dumps_call(original_node.value):
                    self.node_and_replacement = (
                        original_node.value,
                        self._fix_json_dumps(original_node.value),
                    )
                # make_response(...)
                elif maybe_make_response := self._is_make_response_with_json(
                    original_node.value
                ):
                    if maybe_dict := self._has_dict_with_headers_mr_call(
                        maybe_make_response
                    ):
                        if not self._has_content_type_key(maybe_dict):
                            self.node_and_replacement = (
                                maybe_dict,
                                self._fix_dict(maybe_dict),
                            )
                    else:
                        first_arg = maybe_make_response.args[0].value
                        match first_arg:
                            case cst.Tuple():
                                self.node_and_replacement = (
                                    first_arg,
                                    self._fix_tuple(first_arg),
                                )
                            case _:
                                self.node_and_replacement = (
                                    maybe_make_response,
                                    self._fix_make_response(maybe_make_response),
                                )

                # return (...,...)
                elif maybe_tuple := self._is_tuple_with_json_string_response(
                    original_node.value
                ):
                    if maybe_dict := self._has_dict_with_headers(maybe_tuple):
                        if not self._has_content_type_key(maybe_dict):
                            self.node_and_replacement = (
                                maybe_dict,
                                self._fix_dict(maybe_dict),
                            )
                    else:
                        self.node_and_replacement = (
                            maybe_tuple,
                            self._fix_tuple(maybe_tuple),
                        )

    def _is_tuple_with_json_string_response(
        self, node: cst.CSTNode
    ) -> Optional[cst.Tuple]:
        match node:
            case cst.Tuple():
                elements = node.elements
                first = elements[0].value
                maybe_vuln = self._is_json_dumps_call(
                    first
                ) or self._is_make_response_with_json(first)
                if maybe_vuln:
                    return node
        return None

    def _has_dict_with_headers(self, node: cst.Tuple) -> Optional[cst.Dict]:
        elements = list(node.elements)
        last = elements[-1].value
        last = self.resolve_expression(last)
        match last:
            case cst.Dict():
                return last
        return None

    def _build_dict(self) -> cst.Dict:
        return cst.Dict(
            [
                cst.DictElement(
                    cst.SimpleString(f"'{self.content_type_key}'"),
                    cst.SimpleString(f"'{self.json_content_type}'"),
                )
            ]
        )

    def _has_route_decorator(self, node: cst.FunctionDef) -> bool:
        # We cannot guarantee that this decorator originates from a flask app object
        # thus we just check for the name
        for decorator in node.decorators:
            match decorator.decorator:
                case cst.Call(func=cst.Attribute() as func):
                    if func.attr.value == "route":
                        return True
        return False

    def _is_json_dumps_call(self, node: cst.BaseExpression) -> Optional[cst.Call]:
        expr = self.resolve_expression(node)
        match expr:
            case cst.Call():
                true_name = self.find_base_name(expr)
                if true_name == "json.dumps":
                    return expr
        return None

    def _is_make_response_with_json(
        self, node: cst.BaseExpression
    ) -> Optional[cst.Call]:
        expr = self.resolve_expression(node)
        match expr:
            case cst.Call(args=[cst.Arg(first_arg), *_]):
                true_name = self.find_base_name(expr)
                if true_name != "flask.make_response":
                    return None
                match first_arg:
                    case cst.Tuple():
                        first_arg = first_arg.elements[0].value
                if first_arg and self._is_json_dumps_call(first_arg):
                    return expr
        return None

    def _has_dict_with_headers_mr_call(self, call: cst.Call) -> Optional[cst.Dict]:
        first_arg = call.args[0].value
        match first_arg:
            case cst.Tuple():
                return self._has_dict_with_headers(first_arg)
        last = call.args[-1].value
        last = self.resolve_expression(last)
        match last:
            case cst.Dict():
                return last
        return None

    def _has_content_type_key(self, dict_expr: cst.Dict):
        for element in dict_expr.elements:
            match element:
                case cst.StarredDictElement():
                    return True
                case cst.DictElement(key=key):
                    match key:
                        case cst.SimpleString():
                            if key.raw_value == self.content_type_key:
                                return True
                        # it may use variable or other expreesions that resolves to Content-Type
                        case _:
                            return True
        return False

    def _add_key_value(
        self, dict_expr: cst.Dict, key: cst.BaseExpression, value: cst.BaseExpression
    ) -> cst.Dict:
        elements = list(dict_expr.elements)
        elements.append(cst.DictElement(key, value))
        return dict_expr.with_changes(elements=elements)

    def _fix_dict(self, dict_expr: cst.Dict) -> cst.Dict:
        return self._add_key_value(
            dict_expr,
            cst.SimpleString(f"'{self.content_type_key}'"),
            cst.SimpleString(f"'{self.json_content_type}'"),
        )

    def _fix_tuple(self, tuple_expr: cst.Tuple) -> cst.Tuple:
        elements = list(tuple_expr.elements)
        elements.append(cst.Element(self._build_dict()))
        return tuple_expr.with_changes(elements=elements)

    def _fix_make_response(self, call: cst.Call) -> cst.Call:
        args = list(call.args)
        args.append(cst.Arg(self._build_dict()))
        return call.with_changes(args=args)

    def _fix_json_dumps(self, node: cst.BaseExpression) -> cst.Tuple:
        return cst.Tuple([cst.Element(node), cst.Element(self._build_dict())])
