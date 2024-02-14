import libcst as cst
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod, Reference
from codemodder.codemods.utils_mixin import NameResolutionMixin, AncestorPatternsMixin


class StrConcatInList(SimpleCodemod, NameResolutionMixin, AncestorPatternsMixin):
    metadata = Metadata(
        name="str-concat-in-list",
        summary="TODOReplace Comparisons to Empty Sequence with Implicit Boolean Comparison",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="TODOhttps://docs.python.org/3/library/stdtypes.html#truth-value-testing"
            ),
        ],
    )
    change_description = (
        "todoReplace comparisons to empty sequence with implicit boolean comparison."
    )

    def leave_List(self, original_node: cst.List, updated_node: cst.List) -> cst.List:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node
        return updated_node.with_changes(elements=self.process_elements(original_node))

    def process_elements(self, original_node: cst.List) -> list[cst.Element]:
        new_elements = []
        prev_comma = None
        for element in original_node.elements:
            match element.value:
                case cst.ConcatenatedString():
                    self.report_change(original_node)
                    flattened_parts = self.flatten_concatenated_strings(element.value)
                    for part in flattened_parts:
                        # the very last element should only have a comma if the last element
                        # of the original list had a comma
                        if (
                            element == original_node.elements[-1]
                            and part == flattened_parts[-1]
                        ):
                            new_elements.append(
                                cst.Element(value=part, comma=element.comma)
                            )
                        else:
                            new_elements.append(
                                cst.Element(
                                    value=part, comma=prev_comma or element.comma
                                )
                            )
                case _:
                    prev_comma = element.comma
                    new_elements.append(element)
        return new_elements

    def flatten_concatenated_strings(
        self, concat_node: cst.ConcatenatedString, parts=None
    ):
        if parts is None:
            parts = []

        for node in concat_node.left, concat_node.right:
            match node:
                case cst.ConcatenatedString():
                    self.flatten_concatenated_strings(node, parts)
                case _:
                    parts.append(node)
        return parts
