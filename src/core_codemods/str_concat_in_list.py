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
        new_elements = self.process_elements(original_node)
        return updated_node.with_changes(elements=new_elements)

    def process_elements(self, original_node):
        new_elements = []
        prev_comma = None
        for idx, element in enumerate(original_node.elements):
            if isinstance(element.value, cst.ConcatenatedString):
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
                            cst.Element(value=part, comma=prev_comma or element.comma)
                        )
                    self.report_change(original_node)
            else:
                prev_comma = element.comma
                new_elements.append(element)
        return new_elements

    def flatten_concatenated_strings(
        self, concat_node: cst.ConcatenatedString, parts=None
    ):
        if parts is None:
            parts = []
        if isinstance(concat_node.left, cst.ConcatenatedString):
            self.flatten_concatenated_strings(concat_node.left, parts)
        else:
            parts.append(concat_node.left)
        if isinstance(concat_node.right, cst.ConcatenatedString):
            self.flatten_concatenated_strings(concat_node.right, parts)
        else:
            parts.append(concat_node.right)
        return parts
