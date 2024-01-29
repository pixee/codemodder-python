from typing import Union
import libcst as cst
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import (
    Metadata,
    Reference,
    ReviewGuidance,
    SimpleCodemod,
)


class DjangoReceiverOnTop(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="django-receiver-on-top",
        summary="Ensure Django @receiver is the first decorator",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="https://docs.djangoproject.com/en/4.1/topics/signals/"),
        ],
    )
    change_description = "Moved @receiver to the top."

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        # TODO: add filter by include or exclude that works for nodes
        # that that have different start/end numbers.
        maybe_receiver_with_index = None
        for i, decorator in enumerate(original_node.decorators):
            if self.find_base_name(decorator.decorator) == "django.dispatch.receiver":
                maybe_receiver_with_index = (i, decorator)

        if maybe_receiver_with_index:
            index, receiver = maybe_receiver_with_index
            if index > 0:
                new_decorators = [receiver]
                new_decorators.extend(
                    d for d in original_node.decorators if d != receiver
                )
                self.report_change(original_node)
                return updated_node.with_changes(decorators=new_decorators)
        return updated_node
