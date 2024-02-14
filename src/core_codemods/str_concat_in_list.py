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
        new_elements = []
        for element in original_node.elements:
            if isinstance(element.value, cst.ConcatenatedString):
                left_string = cst.Element(value=element.value.left, comma=element.comma)
                right_string = cst.Element(
                    value=element.value.right, comma=element.comma
                )
                new_elements.append(left_string)
                new_elements.append(right_string)

                # depends on line in which they're added
                self.report_change(original_node)
            else:
                new_elements.append(element)
        return updated_node.with_changes(elements=new_elements)
