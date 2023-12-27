import libcst as cst
from libcst import matchers
from codemodder.codemods.api import BaseCodemod, ReviewGuidance
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.codemods.api.helpers import NewArg


class SubprocessShellFalse(BaseCodemod, NameResolutionMixin):
    NAME = "subprocess-shell-false"
    SUMMARY = "Use `shell=False` in `subprocess` Function Calls"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    DESCRIPTION = "Set `shell` keyword argument to `False`"
    REFERENCES: list = []
    SUBPROCESS_FUNCS = [
        f"subprocess.{func}"
        for func in {"run", "call", "check_output", "check_call", "Popen"}
    ]

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if self.find_base_name(original_node.func) in self.SUBPROCESS_FUNCS:
            for arg in original_node.args:
                if matchers.matches(
                    arg.keyword, matchers.Name("shell")
                ) and matchers.matches(arg.value, matchers.Name("True")):
                    self.report_change(original_node)
                    new_args = self.replace_args(
                        original_node,
                        [NewArg(name="shell", value="False", add_if_missing=False)],
                    )
                    return self.update_arg_target(updated_node, new_args)
        return original_node
