from typing import Union

import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.utils.utils import full_qualified_name_from_class, list_subclasses
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class ExceptionWithoutRaiseTransformer(LibcstResultTransformer, NameResolutionMixin):
    change_description = "Raised bare exception statement"

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if not self.node_is_selected(original_node):
            return updated_node

        match original_node:
            case cst.SimpleStatementLine(
                body=[cst.Expr(cst.Name() | cst.Attribute() as name)]
            ):
                if self._is_subclass_of_base_exception(name):
                    self.report_change(original_node)
                    return updated_node.with_changes(body=[cst.Raise(exc=name)])
            case cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        cst.Call(func=cst.Name() | cst.Attribute() as name)
                    ) as call
                ]
            ):
                if self._is_subclass_of_base_exception(name):
                    self.report_change(original_node)
                    return updated_node.with_changes(body=[cst.Raise(exc=call)])
        return updated_node

    def _is_subclass_of_base_exception(self, name: cst.Name | cst.Attribute) -> bool:
        true_name = self.find_base_name(name)
        all_exceptions = [
            full_qualified_name_from_class(kls)
            for kls in list_subclasses(BaseException)
        ]
        if true_name in all_exceptions:
            return True
        return False


ExceptionWithoutRaise = CoreCodemod(
    metadata=Metadata(
        name="exception-without-raise",
        summary="Ensure bare exception statements are raised",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/tutorial/errors.html#raising-exceptions"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(ExceptionWithoutRaiseTransformer),
    detector=None,
)
