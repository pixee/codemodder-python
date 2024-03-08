import libcst as cst
from libcst.metadata import PositionProvider

from codemodder.codemods.libcst_transformer import LibcstResultTransformer
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class FixDataclassDefaults(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="fix-dataclass-defaults",
        summary="todo",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/dataclasses.html#mutable-default-values"
            )
        ],
    )
    change_description = "todo"

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:

        for decorator in original_node.decorators:
            if self.find_base_name(decorator.decorator) == "dataclass.dataclass":
                mod = FieldTransformer(
                    self.context, results=None, file_context=self.file_context
                )

                new_class = original_node.visit(mod)

                if mod.needs_import:
                    self.add_needed_import("dataclass", "field")
                return new_class
        return updated_node


class FieldTransformer(LibcstResultTransformer):
    """
    Converts mutable default values in dataclass fields to use default_factory.
    """

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self,
        *codemod_args,
        **codemod_kwargs,
    ) -> None:
        LibcstResultTransformer.__init__(self, *codemod_args, **codemod_kwargs)
        self.needs_import = False

    def leave_AnnAssign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.CSTNode:
        match original_node.value:
            case cst.List(elements=[]) | cst.Dict(elements=[]) | cst.Tuple(elements=[]):
                self.needs_import = True
                self.report_change(original_node)
                return updated_node.with_changes(
                    value=cst.parse_expression(
                        f"field(default_factory={ type(original_node.value).__name__.lower()})"
                    )
                )
            case cst.Call(func=cst.Name(value="set")):
                self.needs_import = True
                self.report_change(original_node)
                return updated_node.with_changes(
                    value=cst.parse_expression("field(default_factory=set)")
                )
        return updated_node
