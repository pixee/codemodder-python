import libcst as cst
from libcst import matchers as m

from codemodder.codemods.utils import extract_boolean_operands
from codemodder.codemods.utils_decorators import (
    check_filter_by_path_includes_or_excludes,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, ReviewGuidance, SimpleCodemod


class CombineIsinstanceIssubclass(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="combine-isinstance-issubclass",
        summary="Simplify Boolean Expressions Using `isinstance` and `issubclass`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    )
    change_description = "Use tuple of matches instead of boolean expression"

    @check_filter_by_path_includes_or_excludes
    def leave_BooleanOperation(
        self, original_node: cst.BooleanOperation, updated_node: cst.BooleanOperation
    ) -> cst.CSTNode:
        if self.matches_isinstance_issubclass_or_pattern(original_node):
            self.report_change(original_node)

            elements = []
            seen_values = set()
            for call in extract_boolean_operands(updated_node, ensure_type=cst.Call):
                class_tuple_arg_value = call.args[1].value
                if isinstance(class_tuple_arg_value, cst.Tuple):
                    arg_elements = class_tuple_arg_value.elements
                else:
                    arg_elements = (cst.Element(value=class_tuple_arg_value),)

                for element in arg_elements:
                    if (value := getattr(element.value, "value", None)) in seen_values:
                        # If an element has a non-None evaluated value that has already been seen, continue to avoid duplicates
                        continue
                    if value is not None:
                        seen_values.add(value)
                    elements.append(element)

            instance_arg = updated_node.left.args[0]
            new_class_tuple_arg = cst.Arg(value=cst.Tuple(elements=elements))
            return cst.Call(func=call.func, args=[instance_arg, new_class_tuple_arg])

        return updated_node

    def matches_isinstance_issubclass_or_pattern(
        self, node: cst.BooleanOperation
    ) -> bool:
        # Match the pattern: isinstance(x, cls1) or isinstance(x, cls2) or isinstance(x, cls3) or ...
        # and the same but with issubclass
        args = [m.Arg(value=m.Name()), m.Arg(value=m.Name() | m.Tuple())]
        isinstance_call = m.Call(
            func=m.Name("isinstance"),
            args=args,
        )
        issubclass_call = m.Call(
            func=m.Name("issubclass"),
            args=args,
        )
        isinstance_or = m.BooleanOperation(
            left=isinstance_call, operator=m.Or(), right=isinstance_call
        )
        issubclass_or = m.BooleanOperation(
            left=issubclass_call, operator=m.Or(), right=issubclass_call
        )

        # Check for simple case: isinstance(x, cls) or issubclass(x, cls)
        if (
            m.matches(node, isinstance_or | issubclass_or)
            and node.left.func.value == node.right.func.value  # Same function
            and node.left.args[0].value.value
            == node.right.args[0].value.value  # Same first argument (instance)
        ):
            return True

        # Check for chained case: isinstance(x, cls1) or isinstance(x, cls2) or isinstance(x, cls3) or ...
        chained_or = m.BooleanOperation(
            left=m.BooleanOperation(operator=m.Or()),
            operator=m.Or(),
            right=isinstance_call | issubclass_call,
        )
        if m.matches(node, chained_or):
            return all(
                (
                    call.func.value == node.right.func.value  # Same function
                    and call.args[0].value.value
                    == node.right.args[0].value.value  # Same first argument (instance)
                )
                for call in extract_boolean_operands(node, ensure_type=cst.Call)
            )

        # No match
        return False
