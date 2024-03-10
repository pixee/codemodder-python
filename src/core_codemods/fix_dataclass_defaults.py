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
        maybe_has_decorator = (
            self._has_dataclass_decorator(maybe_classdef) if maybe_classdef else False
        )
        if not maybe_has_decorator:
            return updated_node

        match original_node.value:
            # TODO: add support for populated elements
            case cst.List(elements=[]) | cst.Dict(elements=[]) | cst.Tuple(elements=[]):
                self.add_needed_import("dataclasses", "field")
                self.report_change(original_node)
                return updated_node.with_changes(
                    value=cst.parse_expression(
                        f"field(default_factory={ type(original_node.value).__name__.lower()})"
                    )
                )
            case cst.Call(func=cst.Name(value="set"), args=[]):
                self.add_needed_import("dataclasses", "field")
                self.report_change(original_node)
                return updated_node.with_changes(
                    value=cst.parse_expression("field(default_factory=set)")
                )
        return updated_node

    def _has_dataclass_decorator(self, node: cst.ClassDef) -> bool:
        for decorator in node.decorators:
            if self.find_base_name(decorator.decorator) == "dataclasses.dataclass":
                return True
        return False
