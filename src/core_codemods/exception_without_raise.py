from typing import Union
import libcst as cst
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance

from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.utils.utils import list_subclasses


class ExceptionWithoutRaise(BaseCodemod, NameResolutionMixin):
    NAME = "exception-without-raise"
    SUMMARY = "Added raise statement to exception creation"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = SUMMARY
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/tutorial/errors.html#raising-exceptions",
            "description": "",
        },
    ]
    CHANGE_DESCRIPTION = "Wrapped exception in a raise statement"

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> Union[
        cst.BaseStatement, cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel
    ]:
        match original_node:
            case cst.SimpleStatementLine(
                body=[cst.Expr(cst.Name() | cst.Attribute() as name)]
            ):
                true_name = self.find_base_name(name)
                if true_name:
                    true_name = true_name.split(".")[-1]
                all_exceptions = list_subclasses(BaseException)
                if true_name in all_exceptions:
                    self.report_change(original_node)
                    return updated_node.with_changes(body=[cst.Raise(exc=name)])
        return updated_node
