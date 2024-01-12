import libcst as cst
from libcst import matchers as m
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin


class CombineStartswithEndswith(BaseCodemod, NameResolutionMixin):
    NAME = "combine-startswith-endswith"
    SUMMARY = "Simplify Boolean Expressions Using `startswith` and `endswith`"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Use tuple of matches instead of boolean expression"
    REFERENCES: list = []

    def leave_BooleanOperation(
        self, original_node: cst.BooleanOperation, updated_node: cst.BooleanOperation
    ) -> cst.CSTNode:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if self.matches_startswith_endswith_or_pattern(original_node):
            left_call = cst.ensure_type(updated_node.left, cst.Call)
            right_call = cst.ensure_type(updated_node.right, cst.Call)

            self.report_change(original_node)

            new_arg = cst.Arg(
                value=cst.Tuple(
                    elements=[
                        cst.Element(value=left_call.args[0].value),
                        cst.Element(value=right_call.args[0].value),
                    ]
                )
            )

            return cst.Call(func=left_call.func, args=[new_arg])

        return updated_node

    def matches_startswith_endswith_or_pattern(
        self, node: cst.BooleanOperation
    ) -> bool:
        # Match the pattern: x.startswith("...") or x.startswith("...")
        # and the same but with endswith
        args = [m.Arg(value=m.SimpleString())]
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

        return (
            m.matches(node, startswith_or | endswith_or)
            and node.left.func.value.value == node.right.func.value.value
        )
