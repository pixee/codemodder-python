from libcst.metadata import PositionProvider
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.change import Change
from codemodder.codemods.transformations.clean_imports import (
    GatherTopLevelImportBlocks,
    OrderImportsBlocksTransform,
)
import libcst as cst
from libcst.codemod import Codemod, CodemodContext


class OrderImports(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Formats and orders imports by categories."),
        NAME="order-imports",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        REFERENCES=[],
    )
    SUMMARY = "Order Imports"
    CHANGE_DESCRIPTION = "Ordered and formatted import block below this line"

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, codemod_context: CodemodContext, *codemod_args):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, *codemod_args)

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
                    line_number = self.node_position(
                        top_imports_visitor.top_imports_blocks[i][0]
                    ).start.line
                    self.file_context.codemod_changes.append(
                        Change(line_number, self.CHANGE_DESCRIPTION)
                    )
            return result_tree
        return tree

    def filter_by_path_includes_or_excludes(self, pos_to_match):
        """
        Returns False if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(PositionProvider, node)


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line
