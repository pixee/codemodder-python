from typing import Union
import libcst as cst
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import (
    Metadata,
    Reference,
    ReviewGuidance,
)
from core_codemods.api.core_codemod import CoreCodemod


class DjangoModelWithoutDunderStrTransformer(
    LibcstResultTransformer, NameResolutionMixin
):
    change_description = "todoMoved @receiver to the top."

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

        dunder_str = cst.FunctionDef(
            leading_lines=[cst.EmptyLine(indent=False)],
            name=cst.Name("__str__"),
            params=cst.Parameters(params=[cst.Param(name=cst.Name("self"))]),
            body=cst.IndentedBlock(body=[cst.SimpleStatementLine(body=[cst.Pass()])]),
        )
        new_body = updated_node.body.with_changes(
            body=[*updated_node.body.body, dunder_str]
        )

        return updated_node.with_changes(body=new_body)

    def implements_dunder_str(self, original_node: cst.ClassDef) -> bool:
        for node in original_node.body.body:
            match node:
                case cst.FunctionDef(name=cst.Name(value="__str__")):
                    return True
        return False


DjangoModelWithoutDunderStr = CoreCodemod(
    metadata=Metadata(
        name="django-model-without-dunder-str",
        summary="TODOEnsure Django @receiver is the first decorator",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="todohttps://docs.djangoproject.com/en/4.1/topics/signals/"),
        ],
    ),
    transformer=LibcstTransformerPipeline(DjangoModelWithoutDunderStrTransformer),
    detector=None,
)
