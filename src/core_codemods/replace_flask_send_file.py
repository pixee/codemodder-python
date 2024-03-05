from typing import Optional

import libcst as cst

from codemodder.codemods.utils import BaseType, infer_expression_type
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.utils.utils import positional_to_keyword
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class ReplaceFlaskSendFile(SimpleCodemod, NameAndAncestorResolutionMixin):
    metadata = Metadata(
        name="replace-flask-send-file",
        summary="Replace unsafe usage of `flask.send_file`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://flask.palletsprojects.com/en/3.0.x/api/#flask.send_from_directory"
            ),
            Reference(url="https://owasp.org/www-community/attacks/Path_Traversal"),
        ],
    )

    change_description = (
        "Replace unsafe usage of `flask.send_file` with `flask.send_from_directory`"
    )

    pos_to_key_map: list[str | None] = [
        "mimetype",
        "as_attachment",
        "download_name",
        "conditional",
        "etag",
        "last_modified",
        "max_age",
    ]

    def leave_Call(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.BaseExpression:
        if self.filter_by_path_includes_or_excludes(original_node):
            maybe_base_name = self.find_base_name(original_node)
            if maybe_base_name and maybe_base_name == "flask.send_file":
                maybe_tuple = self.parameterize_path(original_node.args[0])
                if maybe_tuple:
                    new_args = [
                        maybe_tuple[0],
                        maybe_tuple[1],
                        *positional_to_keyword(
                            original_node.args[1:], self.pos_to_key_map
                        ),
                    ]
                    self.report_change(original_node)
                    self.add_needed_import("flask")
                    self.remove_unused_import(original_node)
                    new_func = cst.parse_expression("flask.send_from_directory")
                    return updated_node.with_changes(func=new_func, args=new_args)

        return updated_node

    def _wrap_in_path(self, expr) -> cst.Call:
        self.add_needed_import("pathlib", "Path")
        return cst.Call(func=cst.Name(value="Path"), args=[cst.Arg(expr)])

    def _attribute_reference(self, expr, attribute: str) -> cst.Attribute:
        return cst.Attribute(value=expr, attr=cst.Name(attribute))

    def _build_args(self, expr):
        return (
            cst.Arg(self._attribute_reference(expr, "parent")),
            cst.Arg(self._attribute_reference(expr, "name")),
        )

    def _build_args_with_named_expr(self, expr):
        available_name = self.generate_available_name(expr, ["p"])
        named_expr = cst.NamedExpr(
            target=cst.Name(available_name),
            value=expr,
            lpar=[cst.LeftParen()],
            rpar=[cst.RightParen()],
        )
        return (
            cst.Arg(self._attribute_reference(named_expr, "parent")),
            cst.Arg(self._attribute_reference(cst.Name(available_name), "name")),
        )

    def _build_args_with_path_and_named_expr(self, expr):
        available_name = self.generate_available_name(expr, ["p"])
        named_expr = cst.NamedExpr(
            target=cst.Name(available_name),
            value=self._wrap_in_path(expr),
            lpar=[cst.LeftParen()],
            rpar=[cst.RightParen()],
        )
        return (
            cst.Arg(self._attribute_reference(named_expr, "parent")),
            cst.Arg(self._attribute_reference(cst.Name(available_name), "name")),
        )

    def parameterize_path(self, arg: cst.Arg) -> Optional[tuple[cst.Arg, cst.Arg]]:
        expr = self.resolve_expression(arg.value)
        tipo = infer_expression_type(expr)
        # is it a string?
        # TODO support for infering types from string methods e.g. 'a'.capitalize()
        match tipo:
            case BaseType.STRING:
                return self._build_args_with_path_and_named_expr(arg.value)

        # is it a Path object?
        # TODO support for identifying Path operators/function e.g. Path('1') / Path('2')
        match expr:
            case cst.Call():
                base_name = self.find_base_name(expr)
                if base_name and base_name == "pathlib.Path":
                    if arg.value is expr:
                        return self._build_args_with_named_expr(arg.value)
                    return self._build_args(arg.value)

        return None
