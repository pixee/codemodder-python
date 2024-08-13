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
        # Todo: add filter logic

        if isinstance(updated_node.operator, cst.Not) and isinstance(
            updated_node.expression, cst.Comparison
        ):
            comparison = updated_node.expression

            if len(comparison.comparisons) == 1:
                comp_op = comparison.comparisons[0].operator
                # Handle 'not status is True' -> 'not status'
                if (
                    isinstance(comp_op, cst.Is)
                    and comparison.comparisons[0].comparator.value == "True"
                ):
                    self.report_change(original_node)
                    return cst.UnaryOperation(
                        operator=cst.Not(), expression=comparison.left
                    )

                # Handle 'not status is False' -> 'status'
                if (
                    isinstance(comp_op, cst.Is)
                    and comparison.comparisons[0].comparator.value == "False"
                ):
                    self.report_change(original_node)
                    return comparison.left

            # Invert other comparison operators
            inverted_comparisons = []
            for comparison_op in comparison.comparisons:
                if isinstance(comparison_op.operator, cst.Equal):
                    inverted_comparisons.append(
                        comparison_op.with_changes(operator=cst.NotEqual())
                    )
                elif isinstance(comparison_op.operator, cst.NotEqual):
                    inverted_comparisons.append(
                        comparison_op.with_changes(operator=cst.Equal())
                    )
                elif isinstance(comparison_op.operator, cst.LessThan):
                    inverted_comparisons.append(
                        comparison_op.with_changes(operator=cst.GreaterThanEqual())
                    )
                elif isinstance(comparison_op.operator, cst.GreaterThan):
                    inverted_comparisons.append(
                        comparison_op.with_changes(operator=cst.LessThanEqual())
                    )
                elif isinstance(comparison_op.operator, cst.LessThanEqual):
                    inverted_comparisons.append(
                        comparison_op.with_changes(operator=cst.GreaterThan())
                    )
                elif isinstance(comparison_op.operator, cst.GreaterThanEqual):
                    inverted_comparisons.append(
                        comparison_op.with_changes(operator=cst.LessThan())
                    )
                else:
                    inverted_comparisons.append(comparison_op)
            self.report_change(original_node)
            return cst.Comparison(
                left=comparison.left, comparisons=inverted_comparisons
            )

        return updated_node


InvertedBooleanCheck = CoreCodemod(
    metadata=Metadata(
        name="invert-boolean-check",
        summary="Invert Boolean Check",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[],
    ),
    transformer=LibcstTransformerPipeline(InvertedBooleanCheckTransformer),
)
