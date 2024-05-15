from typing import Optional

import libcst as cst
from libcst import ensure_type, matchers

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class TempfileMktempTransformer(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):
    change_description = "Replaces `tempfile.mktemp` with `tempfile.mkstemp`."
    _module_name = "tempfile"

    def leave_SimpleStatementLine(self, original_node, updated_node):
        match original_node:
            case cst.SimpleStatementLine(body=[bsstmt]):
                block = self.get_parent(original_node)
                # SimpleStatementLine is always part of a IndentedBlock or Module body
                block = ensure_type(block, cst.IndentedBlock | cst.Module)
                if isinstance(block, cst.Module):
                    return self.check_mktemp(original_node, bsstmt)
        return updated_node

    def check_mktemp(
        self, original_node: cst.SimpleStatementLine, bsstmt: cst.BaseSmallStatement
    ) -> cst.SimpleStatementLine | cst.FlattenSentinel:
        if maybe_tuple := self._is_assigned_to_mktemp(bsstmt):  # type: ignore
            assign_name, call = maybe_tuple

            self.report_change(call)
            new_line = cst.parse_statement(
                f"""
with tempfile.NamedTemporaryFile(delete=False) as tf:
    {assign_name} = tf.name
"""
            )
            return cst.FlattenSentinel(
                [
                    new_line,
                ]
            )

        if maybe_tuple := self._mktemp_is_sink(bsstmt):
            wrapper_func_name, call = maybe_tuple
            self.report_change(call)

            new_line = cst.parse_statement(
                f"""
with tempfile.NamedTemporaryFile(delete=False) as tf:
    {wrapper_func_name.value}(tf.name)
"""
            )
            return cst.FlattenSentinel(
                [
                    new_line,
                ]
            )
        return original_node

    def _is_assigned_to_mktemp(
        self, bsstmt: cst.BaseSmallStatement
    ) -> Optional[tuple[cst.AnnAssign | cst.Assign, cst.Call]]:
        match bsstmt:
            case cst.Assign(value=value, targets=targets):
                maybe_value = self._is_mktemp_call(value)  # type: ignore
                if maybe_value and all(
                    map(
                        lambda t: matchers.matches(
                            t, matchers.AssignTarget(target=matchers.Name())
                        ),
                        targets,  # type: ignore
                    )
                ):
                    # # Todo: handle multiple potential targets
                    return (targets[0], maybe_value)
            case cst.AnnAssign(target=target, value=value):
                maybe_value = self._is_mktemp_call(value)  # type: ignore
                if maybe_value and isinstance(target, cst.Name):  # type: ignore
                    return (target, maybe_value)
        return None

    def _is_mktemp_call(self, value) -> Optional[cst.Call]:
        match value:
            case cst.Call() if self.find_base_name(value.func) == "tempfile.mktemp":
                return value
        return None

    def _mktemp_is_sink(
        self, bsstmt: cst.BaseSmallStatement
    ) -> Optional[tuple[cst.AnnAssign | cst.Assign, cst.Call]]:
        match bsstmt:
            case cst.Expr(value=cst.Call() as call):
                if not (args := call.args):
                    return None

                # todo: handle more complex cases of mktemp in different arg pos
                match first_arg_call := args[0].value:
                    case cst.Call():
                        if maybe_value := self._is_mktemp_call(first_arg_call):  # type: ignore
                            wrapper_func = call.func
                            return (wrapper_func, maybe_value)
        return None


TempfileMktemp = CoreCodemod(
    metadata=Metadata(
        name="secure-tempfile",
        summary="Upgrade and Secure Temp File Creation",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/tempfile.html#tempfile.mktemp"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(TempfileMktempTransformer),
)
