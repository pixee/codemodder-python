import libcst as cst

from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FixDataclassDefaults(SimpleCodemod, NameAndAncestorResolutionMixin, UtilsMixin):
    metadata = Metadata(
        name="fix-dataclass-defaults",
        summary="Replace `dataclass` Mutable Default Values with Call to `field`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/dataclasses.html#mutable-default-values"
            )
        ],
    )
    change_description = (
        "Replace `dataclass` mutable default values with call to `field`"
    )

    def leave_AnnAssign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.CSTNode:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        maybe_classdef = self.find_immediate_class_def(original_node)
        if not (
            self._has_dataclass_decorator(maybe_classdef) if maybe_classdef else False
        ):
            return updated_node

        match original_node.value:
            case cst.List(elements=[]) | cst.Dict(elements=[]) | cst.Tuple(elements=[]):
                return self.field_with_default_factory(original_node, updated_node)
            case (
                cst.List(elements=[_, *_])
                | cst.Dict(elements=[_, *_])
                | cst.Tuple(elements=[_, *_])
            ):
                return self.field_with_default_factory(
                    original_node, updated_node, empty=False
                )
            case cst.Call(func=cst.Name(value="set"), args=[]):
                return self.field_with_default_factory(original_node, updated_node)
            case cst.Call(func=cst.Name(value="set"), args=[_, *_]):
                return self.field_with_default_factory(
                    original_node, updated_node, empty=False
                )
        return updated_node

    def field_with_default_factory(
        self,
        original_node: cst.List | cst.Tuple | cst.Dict | cst.Call,
        updated_node: cst.List | cst.Tuple | cst.Dict | cst.Call,
        empty=True,
    ):
        self.add_needed_import("dataclasses", "field")
        self.report_change(original_node)
        value = original_node.value
        if empty:
            expr = (
                "field(default_factory=set)"
                if isinstance(value, cst.Call)
                else f"field(default_factory={type(value).__name__.lower()})"
            )
            return updated_node.with_changes(value=cst.parse_expression(expr))

        expr = f"field(default_factory=lambda: {self.code(value).strip()})"
        return updated_node.with_changes(value=cst.parse_expression(expr))

    def _has_dataclass_decorator(self, node: cst.ClassDef) -> bool:
        for decorator in node.decorators:
            if self.find_base_name(decorator.decorator) == "dataclasses.dataclass":
                return True
        return False
