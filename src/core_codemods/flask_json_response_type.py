from typing import Optional, Union
import libcst as cst
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

    def leave_Return(
        self, original_node: cst.Return, updated_node: cst.Return
    ) -> Union[
        cst.BaseSmallStatement,
        cst.FlattenSentinel[cst.BaseSmallStatement],
        cst.RemovalSentinel,
    ]:
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
                maybe_json_dumps = self._is_json_dumps_call(original_node.value)
                if maybe_json_dumps:
                    self.add_change(original_node, self.CHANGE_DESCRIPTION)
                    return updated_node.with_changes(
                        value=self._wrap_into_tuple_with_content_type(
                            original_node.value
                        )
                    )

                # make_response(json.dumps(...),...)
                maybe_make_response = self.is_make_response_with_json(
                    original_node.value
                )
                if maybe_make_response:
                    self.add_change(original_node, self.CHANGE_DESCRIPTION)
                    return updated_node.with_changes(
                        value=self._wrap_into_tuple_with_content_type(
                            original_node.value
                        )
                    )

                # tuple case
                match original_node.value:
                    case cst.Tuple():
                        maybe_fixed_tuple = self._fix_response_tuple(
                            original_node.value
                        )
                        if maybe_fixed_tuple:
                            self.add_change(original_node, self.CHANGE_DESCRIPTION)
                            return updated_node.with_changes(value=maybe_fixed_tuple)
        return updated_node

    def _is_string_or_int(self, node: cst.BaseExpression):
        expr = self.resolve_expression(node)
        if expr and isinstance(expr, cst.SimpleString | cst.Integer):
            return True
        return False

    def _fix_response_tuple(self, node: cst.Tuple) -> Optional[cst.Tuple]:
        elements = list(node.elements)
        # (make_response | json.dumps, ..., {...})
        if len(elements) == 3:
            last = elements[-1].value
            match last:
                case cst.Dict() if not self._has_content_type_key(last):
                    elements[-1] = cst.Element(
                        self._add_key_value(
                            last,
                            cst.SimpleString(f"'{self.content_type_key}'"),
                            cst.SimpleString(f"'{self.json_content_type}'"),
                        )
                    )
                    return node.with_changes(elements=elements)
        # (make_response | json.dumps, string|number)
        # (make_response | json.dumps, {...})
        if len(elements) == 2:
            last = elements[-1].value
            expr = self.resolve_expression(last)
            match expr:
                case cst.Dict() if not self._has_content_type_key(expr):
                    if last == expr:
                        elements[-1] = cst.Element(
                            self._add_key_value(
                                expr,
                                cst.SimpleString(f"'{self.content_type_key}'"),
                                cst.SimpleString(f"'{self.json_content_type}'"),
                            )
                        )
                        return node.with_changes(elements=elements)
                    # TODO  last != expr case.
                case cst.Integer() | cst.SimpleString():
                    elements.append(cst.Element(self._build_dict()))
                    return node.with_changes(elements=elements)
        return None

    def _wrap_into_tuple_with_content_type(self, node: cst.BaseExpression) -> cst.Tuple:
        return cst.Tuple([cst.Element(node), cst.Element(self._build_dict())])

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
        expr = node
        match node:
            case cst.Name():
                expr = self._resolve_name_transitive(node)
        match expr:
            case cst.Call():
                true_name = self.find_base_name(expr)
                if true_name == "json.dumps":
                    return expr
        return None

    def is_make_response_with_json(
        self, node: cst.BaseExpression
    ) -> Optional[cst.Call]:
        expr = node
        match node:
            case cst.Name():
                expr = self._resolve_name_transitive(node)
        match expr:
            case cst.Call():
                true_name = self.find_base_name(expr)
                if true_name != "flask.make_response":
                    return None
                first_arg = expr.args[0].value if expr.args else None
                if first_arg and self._is_json_dumps_call(first_arg):
                    return expr
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
