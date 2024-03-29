import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class FixMissingSelfOrClsTransformer(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):
    change_description = "Add `self` or `cls` parameter to instance or class method."

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        if not self.node_is_selected(original_node):
            return original_node

        if not self.find_immediate_class_def(original_node):
            # If `original_node` is not inside a class, nothing to do.
            return original_node

        if self.find_immediate_function_def(original_node):
            # If `original_node` is inside a class but also nested within a function/method
            # We won't touch it.
            return original_node

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


FixMissingSelfOrCls = CoreCodemod(
    metadata=Metadata(
        name="fix-missing-self-or-cls",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        summary="Add Missing Positional Parameter for Instance and Class Methods",
        references=[],
    ),
    transformer=LibcstTransformerPipeline(FixMissingSelfOrClsTransformer),
    detector=None,
)
