import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from core_codemods.api import CoreCodemod, Metadata, ReviewGuidance


class InvertedBooleanCheckTransformer(LibcstResultTransformer):
    change_description = "Flips inverted boolean check."

    def leave_UnaryOperation(
        self, original_node: cst.UnaryOperation, updated_node: cst.UnaryOperation
    ) -> cst.BaseExpression:
        if not self.node_is_selected(original_node):
            return updated_node

        if isinstance(updated_node.operator, cst.Not) and isinstance(
            (comparison := updated_node.expression), cst.Comparison
        ):
            return self.report_new_comparison(original_node, comparison)
        return updated_node

    def report_new_comparison(
        self, original_node: cst.UnaryOperation, comparison: cst.Comparison
    ) -> cst.BaseExpression:
        if len(comparison.comparisons) == 1 and isinstance(
            comparison.comparisons[0].operator, cst.Is
        ):
            # Handle 'not status is True' -> 'not status'
            if comparison.comparisons[0].comparator.value == "True":
                self.report_change(original_node)
                return cst.UnaryOperation(
                    operator=cst.Not(), expression=comparison.left
                )

            # Handle 'not status is False' -> 'status'
            if comparison.comparisons[0].comparator.value == "False":
                self.report_change(original_node)
                return comparison.left

        inverted_comparisons = self._invert_comparisons(comparison)

        self.report_change(original_node)
        return cst.Comparison(left=comparison.left, comparisons=inverted_comparisons)

    def _invert_comparisons(
        self, comparison: cst.Comparison
    ) -> list[cst.ComparisonTarget]:
        inverted_comparisons = []
        for comparison_op in comparison.comparisons:
            match comparison_op.operator:
                case cst.Equal():
                    new_operator = cst.NotEqual()
                case cst.NotEqual():
                    new_operator = cst.Equal()
                case cst.LessThan():
                    new_operator = cst.GreaterThanEqual()
                case cst.GreaterThan():
                    new_operator = cst.LessThanEqual()
                case cst.LessThanEqual():
                    new_operator = cst.GreaterThan()
                case cst.GreaterThanEqual():
                    new_operator = cst.LessThan()
                case _:
                    new_operator = comparison_op

            inverted_comparisons.append(
                comparison_op.with_changes(operator=new_operator)
            )
        return inverted_comparisons


InvertedBooleanCheck = CoreCodemod(
    metadata=Metadata(
        name="invert-boolean-check",
        summary="Invert Boolean Check",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    ),
    transformer=LibcstTransformerPipeline(InvertedBooleanCheckTransformer),
)
