import libcst as cst
from libcst.metadata import PositionProvider

from codemodder.codemods.base_visitor import UtilsMixin
from codemodder.codemods.transformations.clean_imports import (
    GatherTopLevelImportBlocks,
    OrderImportsBlocksTransform,
)
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class OrderImports(SimpleCodemod, UtilsMixin):
    metadata = Metadata(
        name="order-imports",
        summary="Order Imports",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        description="",
    )
    change_description = "Ordered and formatted import block below this line"

    METADATA_DEPENDENCIES = (PositionProvider,)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        top_imports_visitor = GatherTopLevelImportBlocks()
        tree.visit(top_imports_visitor)

        # Filter import blocks by line includes/excludes within their anchors
        filtered_blocks = []
        for block in top_imports_visitor.top_imports_blocks:
            anchor = block[0]
            anchor_pos = self.node_position(anchor)
            if self.filter_by_path_includes_or_excludes(anchor_pos):
                filtered_blocks.append(block)
        if filtered_blocks:
            order_transformer = OrderImportsBlocksTransform(
                self.file_context.base_directory,
                filtered_blocks,
            )
            result_tree = tree.visit(order_transformer)

            # seemingly redundant, this check makes it possible to return the original tree
            for i, changed in enumerate(order_transformer.changes):
                if changed:
                    self.add_change(
                        top_imports_visitor.top_imports_blocks[i][0],
                        self.change_description,
                    )
            return result_tree
        return tree
