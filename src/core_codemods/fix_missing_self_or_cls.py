import libcst as cst

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class FixMissingSelfOrCls(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="fix-missing-self-or-cls",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        summary="todo",
        references=[],
    )

    change_description = "todo"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_class_name = None

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.current_class_name = node.name.value
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.current_class_name = None
        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        if self.current_class_name:
            if original_node.decorators:
                if self.is_staticmethod(original_node):
                    return updated_node
                if self.is_classmethod(original_node):
                    if self.has_no_args(original_node):
                        self.report_change(original_node)
                        return updated_node.with_changes(
                            params=updated_node.params.with_changes(
                                params=[cst.Param(name=cst.Name("cls"))]
                            )
                        )
            else:
                if self.has_no_args(original_node):
                    self.report_change(original_node)
                    return updated_node.with_changes(
                        params=updated_node.params.with_changes(
                            params=[cst.Param(name=self._pick_arg_name(original_node))]
                        )
                    )
        return updated_node

    def _pick_arg_name(self, node: cst.FunctionDef) -> cst.Name:
        match node.name:
            case cst.Name(value="__new__") | cst.Name(value="__init_subclass__"):
                new_name = "cls"
            case _:
                new_name = "self"
        return cst.Name(value=new_name)

    def has_no_args(self, node: cst.FunctionDef) -> bool:
        converted_star_arg = (
            None
            if node.params.star_arg is cst.MaybeSentinel.DEFAULT
            else node.params.star_arg
        )
        return not any(
            (
                node.params.params,
                converted_star_arg,
                node.params.kwonly_params,
                node.params.star_kwarg,
                node.params.posonly_params,
            )
        )
