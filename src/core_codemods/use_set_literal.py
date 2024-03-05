import libcst as cst

from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class UseSetLiteral(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="use-set-literal",
        summary="Use Set Literals Instead of Sets from Lists",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Replace sets from lists with set literals"

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        match original_node.func:
            case cst.Name("set"):
                if self.is_builtin_function(original_node):
                    match original_node.args:
                        case [cst.Arg(value=cst.List(elements=elements))]:
                            self.report_change(original_node)

                            # Can't use set literal for empty set
                            if len(elements) == 0:
                                return updated_node.with_changes(args=[])

                            return cst.Set(elements=elements)

        return updated_node
