from typing import Union
import libcst as cst
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance

from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.utils.utils import full_qualified_name_from_class, list_subclasses


class ExceptionWithoutRaise(BaseCodemod, NameResolutionMixin):
    NAME = "exception-without-raise"
    SUMMARY = "Ensure bare exception statements are raised"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = SUMMARY
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/tutorial/errors.html#raising-exceptions",
            "description": "",
        },
    ]
    CHANGE_DESCRIPTION = "Raised bare exception statement"

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
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
