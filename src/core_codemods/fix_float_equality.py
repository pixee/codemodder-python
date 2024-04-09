import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class FixFloatEqualityTransformer(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):
    change_description = "Replace `==` or `!=` with `math.isclose`"

    def leave_Comparison(
        self, original_node: cst.Comparison, updated_node: cst.Comparison
    ) -> cst.BaseExpression:
        if not self.node_is_selected(original_node):
            return updated_node

        match original_node:
            case cst.Comparison(
                left=left, comparisons=[cst.ComparisonTarget() as target]
            ):
                if isinstance(
                    target.operator, cst.Equal | cst.NotEqual
                ) and self.at_least_one_float(left, right := target.comparator):
                    self.add_needed_import("math")
                    isclose_call = self.make_isclose_call(left, right)
                    self.report_change(original_node)
                    return (
                        isclose_call
                        if isinstance(target.operator, cst.Equal)
                        else cst.UnaryOperation(
                            operator=cst.Not(),
                            expression=isclose_call,
                        )
                    )
        return updated_node

    def make_isclose_call(self, left, right):
        return cst.Call(
            func=cst.Attribute(
                value=cst.Name(value="math"), attr=cst.Name(value="isclose")
            ),
            args=[
                cst.Arg(value=left),
                cst.Arg(value=right),
                cst.Arg(
                    keyword=cst.Name(value="rel_tol"),
                    value=cst.Float(value="1e-09"),
                    equal=cst.AssignEqual(
                        whitespace_before=cst.SimpleWhitespace(""),
                        whitespace_after=cst.SimpleWhitespace(""),
                    ),
                ),
                cst.Arg(
                    keyword=cst.Name(value="abs_tol"),
                    value=cst.Float(value="0.0"),
                    equal=cst.AssignEqual(
                        whitespace_before=cst.SimpleWhitespace(""),
                        whitespace_after=cst.SimpleWhitespace(""),
                    ),
                ),
            ],
        )

    def at_least_one_float(self, left, right) -> bool:
        left_type = self.resolve_expression(left)
        right_type = self.resolve_expression(right)

        match (left_type, right_type):
            case (cst.Float(), _) | (_, cst.Float()):
                return True
            case (cst.BinaryOperation(), _):
                return self.at_least_one_float(left_type.left, left_type.right)
            case (_, cst.BinaryOperation()):
                return self.at_least_one_float(right_type.left, right_type.right)
        return False


FixFloatEquality = CoreCodemod(
    metadata=Metadata(
        name="fix-float-equality",
        summary="Use `math.isclose` Instead of Direct Equality for Floats",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/tutorial/floatingpoint.html#floating-point-arithmetic-issues-and-limitations"
            ),
            Reference(url="https://docs.python.org/3/library/math.html#math.isclose"),
        ],
    ),
    transformer=LibcstTransformerPipeline(FixFloatEqualityTransformer),
    detector=None,
)
