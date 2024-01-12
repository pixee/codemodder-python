from typing import Union
import libcst as cst
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class DjangoReceiverOnTop(BaseCodemod, NameResolutionMixin):
    NAME = "django-receiver-on-top"
    SUMMARY = "Ensure Django @receiver is the first decorator"
    DESCRIPTION = SUMMARY
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    REFERENCES = [
        {
            "url": "https://docs.djangoproject.com/en/4.1/topics/signals/",
            "description": "",
        },
    ]
    CHANGE_DESCRIPTION = "Moved @receiver to the top."

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        # TODO: add filter by include or exclude that works for nodes
        # that that have different start/end numbers.
        maybe_receiver_with_index = None
        for i, decorator in enumerate(original_node.decorators):
            true_name = self.find_base_name(decorator.decorator)
            if true_name == "django.dispatch.receiver":
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
