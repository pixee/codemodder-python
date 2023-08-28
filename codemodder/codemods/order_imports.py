from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.transformations.clean_imports import OrderTopLevelImports
from codemodder.file_context import FileContext
import libcst as cst
from libcst.codemod import Codemod, CodemodContext
import codemodder.global_state


class OrderImports(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Organize and order imports by categories"),
        NAME="order-imports",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    CHANGE_DESCRIPTION = "Ordered import"

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, file_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        order_codemod = OrderTopLevelImports(
            self.context, codemodder.global_state.DIRECTORY
        )
        return order_codemod.transform_module(tree)
