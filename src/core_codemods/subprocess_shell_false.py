import libcst as cst
from libcst import matchers as m
from libcst.metadata import ParentNodeProvider

from codemodder.codemods.check_annotations import is_disabled_by_annotations
from codemodder.codemods.libcst_transformer import NewArg
from codemodder.codemods.utils_decorators import check_node_is_not_selected
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class SubprocessShellFalse(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="subprocess-shell-false",
        summary="Use `shell=False` in `subprocess` Function Calls",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/subprocess.html#security-considerations"
            ),
            Reference(
                url="https://en.wikipedia.org/wiki/Code_injection#Shell_injection"
            ),
            Reference(url="https://stackoverflow.com/a/3172488"),
        ],
    )
    change_description = "Set `shell` keyword argument to `False`"
    SUBPROCESS_FUNCS = [
        f"subprocess.{func}"
        for func in {"run", "call", "check_output", "check_call", "Popen"}
    ]

    METADATA_DEPENDENCIES = (
        *SimpleCodemod.METADATA_DEPENDENCIES,
        ParentNodeProvider,
    )
    IGNORE_ANNOTATIONS = ["S603"]

    @check_node_is_not_selected
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if (
            self.find_base_name(original_node.func) in self.SUBPROCESS_FUNCS
        ) and not m.matches(
            original_node.args[0],
            m.Arg(
                value=m.SimpleString() | m.ConcatenatedString() | m.FormattedString()
            ),  # First argument to subprocess.<func> cannot be a string or setting shell=False will cause a FileNotFoundError
        ):
            for arg in original_node.args:
                if m.matches(
                    arg,
                    m.Arg(keyword=m.Name("shell"), value=m.Name("True")),
                ) and not is_disabled_by_annotations(
                    original_node,
                    self.metadata,  # type: ignore
                    messages=self.IGNORE_ANNOTATIONS,
                ):
                    self.report_change(original_node)
                    new_args = self.replace_args(
                        original_node,
                        [NewArg(name="shell", value="False", add_if_missing=False)],
                    )
                    return self.update_arg_target(updated_node, new_args)

        return updated_node
