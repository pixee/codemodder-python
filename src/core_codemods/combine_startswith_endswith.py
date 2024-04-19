import libcst as cst
from libcst import matchers as m

from codemodder.codemods.utils import extract_boolean_operands
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class CombineStartswithEndswith(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="combine-startswith-endswith",
        summary="Simplify Boolean Expressions Using `startswith` and `endswith`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Use tuple of matches instead of boolean expression"

    def leave_BooleanOperation(
        self, original_node: cst.BooleanOperation, updated_node: cst.BooleanOperation
    ) -> cst.CSTNode:
        if self.matches_startswith_endswith_or_pattern(original_node):
            if not self.filter_by_path_includes_or_excludes(
                self.node_position(original_node)
            ):
                return updated_node

            self.report_change(original_node)

            elements = []
            seen_evaluated_values = set()
            for call in extract_boolean_operands(updated_node, ensure_type=cst.Call):
                arg_value = call.args[0].value
                if isinstance(arg_value, cst.Tuple):
                    arg_elements = arg_value.elements
                else:
                    arg_elements = (cst.Element(value=arg_value),)

                for element in arg_elements:
                    if (
                        evaluated_value := getattr(
                            element.value, "evaluated_value", None
                        )
                    ) in seen_evaluated_values:
                        # If an element has a non-None evaluated value that has already been seen, continue to avoid duplicates
                        continue
                    if evaluated_value is not None:
                        seen_evaluated_values.add(evaluated_value)
                    elements.append(element)

            new_arg = cst.Arg(value=cst.Tuple(elements=elements))
            return cst.Call(func=call.func, args=[new_arg])

        return updated_node

    def matches_startswith_endswith_or_pattern(
        self, node: cst.BooleanOperation
    ) -> bool:
        # Match the pattern: x.startswith("...") or x.startswith("...") or x.startswith("...") or ...
        # and the same but with endswith
        args = [
            m.Arg(
                value=m.Tuple()
                | m.SimpleString()
                | m.ConcatenatedString()
                | m.FormattedString()
                | m.Name()
            )
        ]
        startswith = m.Call(
            func=m.Attribute(value=m.Name(), attr=m.Name("startswith")),
            args=args,
        )
        endswith = m.Call(
            func=m.Attribute(value=m.Name(), attr=m.Name("endswith")),
            args=args,
        )
        startswith_or = m.BooleanOperation(
            left=startswith, operator=m.Or(), right=startswith
        )
        endswith_or = m.BooleanOperation(left=endswith, operator=m.Or(), right=endswith)

        # Check for simple case: x.startswith("...") or x.startswith("...")
        if (
            m.matches(node, startswith_or | endswith_or)
            and node.left.func.value.value == node.right.func.value.value
        ):
            return True

        # Check for chained case: x.startswith("...") or x.startswith("...") or x.startswith("...") or ...
        chained_or = m.BooleanOperation(
            left=m.BooleanOperation(operator=m.Or()),
            operator=m.Or(),
            right=startswith | endswith,
        )
        if m.matches(node, chained_or):
            return all(
                call.func.value.value == node.right.func.value.value  # Same function
                for call in extract_boolean_operands(node, ensure_type=cst.Call)
            )

        # No match
        return False
