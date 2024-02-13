import libcst as cst
from libcst import matchers
from libcst.metadata import ParentNodeProvider

from codemodder.codemods.check_annotations import is_disabled_by_annotations
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.codemods.libcst_transformer import NewArg
from core_codemods.api import (
    Metadata,
    Reference,
    ReviewGuidance,
    SimpleCodemod,
)


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

    METADATA_DEPENDENCIES = SimpleCodemod.METADATA_DEPENDENCIES + (ParentNodeProvider,)
    IGNORE_ANNOTATIONS = ["S603"]

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(original_node)
        ):
            return updated_node

        if self.find_base_name(original_node.func) in self.SUBPROCESS_FUNCS:
            for arg in original_node.args:
                if matchers.matches(
                    arg,
                    matchers.Arg(
                        keyword=matchers.Name("shell"), value=matchers.Name("True")
                    ),
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
        return original_node
