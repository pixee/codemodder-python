from textwrap import dedent
from typing import Optional

import libcst as cst
from libcst import matchers
from libcst.codemod import CodemodContext
from libcst.metadata import ScopeProvider

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.file_context import FileContext
from codemodder.result import Result, same_line
from codemodder.utils.utils import clean_simplestring
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance


class TempfileMktempTransformer(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):
    change_description = "Replaces `tempfile.mktemp` with `tempfile.mkstemp`."
    _module_name = "tempfile"

    def __init__(
        self,
        context: CodemodContext,
        results: list[Result] | None,
        file_context: FileContext,
        _transformer: bool = False,
    ):
        self.mktemp_calls: set[cst.Call] = set()
        super().__init__(context, results, file_context, _transformer)

    def visit_Call(self, node: cst.Call) -> None:
        self.mktemp_calls.add(node) if self._is_mktemp_call(node) else None

    def leave_SimpleStatementLine(self, original_node, updated_node):
        # todo collapse this method into one below
        match original_node:
            case cst.SimpleStatementLine(body=[bsstmt]):
                return self.check_mktemp(original_node, bsstmt)
        return updated_node

    def check_mktemp(
        self, original_node: cst.SimpleStatementLine, bsstmt: cst.BaseSmallStatement
    ) -> cst.SimpleStatementLine | cst.FlattenSentinel:
        # add include/exclude test

        if not self.node_is_selected(original_node):
            return original_node

        if maybe_tuple := self._is_assigned_to_mktemp(bsstmt):  # type: ignore
            assign_name, call = maybe_tuple
            return self.report_and_change(call, assign_name)
        if maybe_tuple := self._mktemp_is_sink(bsstmt):
            wrapper_func_name, call = maybe_tuple
            return self.report_and_change(call, wrapper_func_name, assignment=False)

        # If we get here it's because there is a mktemp call but we haven't fixed it yet.
        for unfixed in self.mktemp_calls:
            self.report_unfixed(unfixed, reason="Pixee does not yet support this fix.")
        self.mktemp_calls.clear()
        return original_node

    def filter_by_result(self, node) -> bool:
        """
        TODO
        """
        match node:
            case cst.SimpleStatementLine():
                pos_to_match = self.node_position(node)
                return self.results is None or any(
                    self.match_location(pos_to_match, result)
                    for result in self.results or []
                )
        return False

    def match_location(self, pos, result):
        return any(same_line(pos, location) for location in result.locations)

    def report_and_change(
        self, node: cst.Call, name: cst.Name, assignment=True
    ) -> cst.FlattenSentinel:
        self.report_change(node)
        self.add_needed_import(self._module_name)
        self.remove_unused_import(node)
        with_block = (
            f"{name.value} = tf.name" if assignment else f"{name.value}(tf.name)"
        )
        new_stmt = dedent(
            f"""
        with tempfile.NamedTemporaryFile({self._make_args(node)}) as tf:
            {with_block}
        """
        ).rstrip()
        return cst.FlattenSentinel(
            [
                cst.parse_statement(new_stmt),
            ]
        )

    def _make_args(self, node: cst.Call) -> str:
        """Convert args passed to tempfile.mktemp() to string for args to tempfile.NamedTemporaryFile"""

        default = "delete=False"
        if not node.args:
            return default
        new_args = ""
        arg_keys = ("suffix", "prefix", "dir")
        for idx, arg in enumerate(node.args):
            cst.ensure_type(val := arg.value, cst.SimpleString)
            new_args += f'{arg_keys[idx]}="{clean_simplestring(val)}", '
        return f"{new_args}{default}"

    def _is_assigned_to_mktemp(
        self, bsstmt: cst.BaseSmallStatement
    ) -> Optional[tuple[cst.Name, cst.Call]]:
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
                    return (targets[0].target, maybe_value)
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
    ) -> Optional[tuple[cst.Name, cst.Call]]:
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


class GatherMkTempCallsVisitor(cst.CSTVisitor, NameAndAncestorResolutionMixin):
    METADATA_DEPENDENCIES = (ScopeProvider,)

    def __init__(self):
        super().__init__()
        self.calls = []

    def visit_Call(self, node: cst.Call) -> None:
        (
            self.calls.append(node)
            if self.find_base_name(node.func) == "tempfile.mktemp"
            else None
        )


TempfileMktemp = CoreCodemod(
    metadata=Metadata(
        name="secure-tempfile",
        summary="Upgrade and Secure Temp File Creation",
        review_guidance=ReviewGuidance.MERGE_AFTER_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/tempfile.html#tempfile.mktemp"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(TempfileMktempTransformer),
)
