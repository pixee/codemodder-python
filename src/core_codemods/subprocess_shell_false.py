import libcst as cst
from libcst import matchers as m
from libcst.metadata import ParentNodeProvider

from codemodder.codemods.check_annotations import is_disabled_by_annotations
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
    NewArg,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import (
    CoreCodemod,
    Metadata,
    Reference,
    ReviewGuidance,
    SimpleCodemod,
)


class SubprocessShellFalseTransformer(LibcstResultTransformer, NameResolutionMixin):
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

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if not self.node_is_selected(original_node):
            return updated_node

        if self.find_base_name(
            original_node.func
        ) in self.SUBPROCESS_FUNCS and self.first_arg_is_not_string(original_node):
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

    def first_arg_is_not_string(self, original_node: cst.Call) -> bool:
        # First argument to subprocess.<func> cannot be a string or setting shell=False will cause a FileNotFoundError
        return not m.matches(
            original_node.args[0],
            m.Arg(
                value=m.SimpleString() | m.ConcatenatedString() | m.FormattedString()
            ),
        )


SubprocessShellFalse = CoreCodemod(
    metadata=Metadata(
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
    ),
    transformer=LibcstTransformerPipeline(SubprocessShellFalseTransformer),
)
