from typing import Union

import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class DjangoModelWithoutDunderStrTransformer(
    LibcstResultTransformer, NameResolutionMixin
):
    change_description = "Add `__str__` definition to `django` Model class."

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:

        # TODO: add filter by include or exclude that works for nodes
        # that that have different start/end numbers.
        if not any(
            self.find_base_name(base.value) == "django.db.models.Model"
            for base in original_node.bases
        ):
            return updated_node

        if self.implements_dunder_str(original_node):
            return updated_node

        self.report_change(original_node)

        new_body = updated_node.body.with_changes(
            body=[*updated_node.body.body, dunder_str_method()]
        )
        return updated_node.with_changes(body=new_body)

    def implements_dunder_str(self, original_node: cst.ClassDef) -> bool:
        """Check if a ClassDef or its bases implement `__str__`"""
        if self.class_has_method(original_node, "__str__"):
            return True

        for base in original_node.bases:
            if maybe_assignment := self.find_single_assignment(base.value):
                classdef = maybe_assignment.node
                if self.class_has_method(classdef, "__str__"):
                    return True
        return False


def dunder_str_method() -> cst.FunctionDef:
    self_body = cst.IndentedBlock(
        body=[
            cst.parse_statement("model_name = self.__class__.__name__"),
            cst.parse_statement(
                'fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))'
            ),
            cst.parse_statement('return f"{model_name}({fields_str})"'),
        ]
    )
    return cst.FunctionDef(
        leading_lines=[cst.EmptyLine(indent=False)],
        name=cst.Name("__str__"),
        params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
        body=self_body,
    )


DjangoModelWithoutDunderStr = CoreCodemod(
    metadata=Metadata(
        name="django-model-without-dunder-str",
        summary="Ensure Django Model Classes Implement a `__str__` Method",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://docs.djangoproject.com/en/5.0/ref/models/instances/#django.db.models.Model.__str__"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(DjangoModelWithoutDunderStrTransformer),
    detector=None,
)
