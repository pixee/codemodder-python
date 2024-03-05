import libcst as cst

from codemodder.codemods.utils_mixin import AncestorPatternsMixin, NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class StrConcatInSeqLiteral(SimpleCodemod, NameResolutionMixin, AncestorPatternsMixin):
    metadata = Metadata(
        name="str-concat-in-sequence-literals",
        summary="Convert Implicit String Concat Inside Sequence into Individual Elements",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[],
    )
    change_description = "Convert implicit string concat into individual elements."

    def leave_List(self, original_node: cst.List, updated_node: cst.List) -> cst.List:
        return self.process_node_elements(original_node, updated_node)

    def leave_Tuple(
        self, original_node: cst.Tuple, updated_node: cst.Tuple
    ) -> cst.Tuple:
        return self.process_node_elements(original_node, updated_node)

    def leave_Set(self, original_node: cst.Set, updated_node: cst.Set) -> cst.Set:
        return self.process_node_elements(original_node, updated_node)

    def process_node_elements(
        self, original_node: cst.CSTNode, updated_node: cst.CSTNode
    ) -> cst.CSTNode:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node
        return updated_node.with_changes(elements=self._process_elements(original_node))

    def _process_elements(self, original_node: cst.List) -> list[cst.Element]:
        new_elements = []
        prev_comma = None
        for element in original_node.elements:
            match element.value:
                case cst.ConcatenatedString():
                    self.report_change(original_node)
                    flattened_parts = self._flatten_concatenated_strings(element.value)
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

    def _flatten_concatenated_strings(
        self, concat_node: cst.ConcatenatedString, parts=None
    ):
        if parts is None:
            parts = []

        for node in concat_node.left, concat_node.right:
            match node:
                case cst.ConcatenatedString():
                    self._flatten_concatenated_strings(node, parts)
                case _:
                    parts.append(node)
        return parts
