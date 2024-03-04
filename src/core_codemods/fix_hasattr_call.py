import libcst as cst
from core_codemods.api import (
    Metadata,
    Reference,
    ReviewGuidance,
    SimpleCodemod,
)


class TransformFixHasattrCall(SimpleCodemod):
    metadata = Metadata(
        name="fix-hasattr-call",
        summary="todo",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(url="todo"),
        ],
    )
    detector_pattern = """
        - patterns:
          - pattern: hasattr(..., "__call__")
          - pattern-not: $MODULE.hasattr(...)
        """

    change_description = "Replace `hasattr` function call with `callable`"

    def on_result_found(self, original_node, updated_node):
        del original_node
        return updated_node.with_changes(
            func=updated_node.func.with_changes(value="callable"),
            args=[updated_node.args[0].with_changes(comma=cst.MaybeSentinel.DEFAULT)],
        )
