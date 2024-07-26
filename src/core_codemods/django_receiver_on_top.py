from typing import Union

import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class DjangoReceiverOnTopTransformer(LibcstResultTransformer, NameResolutionMixin):
    change_description = "Moved @receiver to the top."

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        maybe_receiver_with_index = None
        for i, decorator in enumerate(original_node.decorators):
            if self.find_base_name(decorator.decorator) == "django.dispatch.receiver":
                maybe_receiver_with_index = (i, decorator)

        if maybe_receiver_with_index and self.node_is_selected(
            maybe_receiver_with_index[1]
        ):
            index, receiver = maybe_receiver_with_index
            if index > 0:
                new_decorators = [receiver]
                new_decorators.extend(
                    d for d in original_node.decorators if d != receiver
                )
                for decorator in new_decorators:
                    self.report_change(decorator)
                return updated_node.with_changes(decorators=new_decorators)
        return updated_node


DjangoReceiverOnTop = CoreCodemod(
    metadata=Metadata(
        name="django-receiver-on-top",
        summary="Ensure Django @receiver is the first decorator",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="https://docs.djangoproject.com/en/4.1/topics/signals/"),
        ],
    ),
    transformer=LibcstTransformerPipeline(DjangoReceiverOnTopTransformer),
    detector=None,
)
