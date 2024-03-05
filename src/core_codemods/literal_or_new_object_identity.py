import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class LiteralOrNewObjectIdentityTransformer(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):
    change_description = "Replace `is` operator with `==`"

    def _is_object_creation_or_literal(self, node: cst.BaseExpression):
        match node:
            case (
                cst.List()
                | cst.Dict()
                | cst.Tuple()
                | cst.Set()
                | cst.Integer()
                | cst.Float()
                | cst.Imaginary()
                | cst.SimpleString()
                | cst.ConcatenatedString()
                | cst.FormattedString()
            ):
                return True
            case cst.Call(func=cst.Name() as name):
                return self.is_builtin_function(node) and name.value in (
                    "dict",
                    "list",
                    "tuple",
                    "set",
                )
        return False

    def leave_Comparison(
        self, original_node: cst.Comparison, updated_node: cst.Comparison
    ) -> cst.BaseExpression:
        match original_node:
            case cst.Comparison(
                left=left, comparisons=[cst.ComparisonTarget() as target]
            ):
                if self.node_is_selected(target.operator) and isinstance(
                    target.operator, cst.Is | cst.IsNot
                ):
                    left = self.resolve_expression(left)
                    right = self.resolve_expression(target.comparator)
                    if self._is_object_creation_or_literal(
                        left
                    ) or self._is_object_creation_or_literal(right):
                        self.report_change(original_node)
                        if isinstance(target.operator, cst.Is):
                            return original_node.with_deep_changes(
                                target,
                                operator=cst.Equal(
                                    whitespace_before=target.operator.whitespace_before,
                                    whitespace_after=target.operator.whitespace_after,
                                ),
                            )
                        return original_node.with_deep_changes(
                            target,
                            operator=cst.NotEqual(
                                whitespace_before=target.operator.whitespace_before,
                                whitespace_after=target.operator.whitespace_after,
                            ),
                        )
        return updated_node


LiteralOrNewObjectIdentity = CoreCodemod(
    metadata=Metadata(
        name="literal-or-new-object-identity",
        summary="Replace `is` with `==` for literal or new object comparisons",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/stdtypes.html#comparisons"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(LiteralOrNewObjectIdentityTransformer),
    detector=None,
)
