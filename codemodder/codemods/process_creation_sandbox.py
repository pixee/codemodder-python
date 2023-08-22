import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.file_context import FileContext
from codemodder.dependency_manager import DependencyManager
from libcst.codemod.visitors import AddImportsVisitor
from codemodder.codemods.change import Change
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.utils import get_call_name

replacement_import = "safe_command"


class ProcessSandbox(SemgrepCodemod, BaseTransformer):
    METADATA = CodemodMetadata(
        DESCRIPTION=(
            "Replaces subprocess.{func} with more secure safe_command library functions."
        ),
        NAME="process-sandbox",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
    )
    CHANGE_DESCRIPTION = "Switch use of subprocess for security.safe_command"
    YAML_FILES = [
        "sandbox_process_creation.yaml",
    ]

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        SemgrepCodemod.__init__(self, file_context)
        BaseTransformer.__init__(
            self,
            codemod_context,
            self._results,
            file_context.line_exclude,
            file_context.line_include,
        )

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            self.CHANGES_IN_FILE.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )
            AddImportsVisitor.add_needed_import(
                self.context, "security", "safe_command"
            )
            DependencyManager().add(["security==1.0.1"])
            new_call = cst.Call(
                func=cst.Attribute(
                    value=cst.Name(value=replacement_import),
                    attr=cst.Name(value=get_call_name(original_node)),
                ),
                args=[cst.Arg(original_node.func), *original_node.args],
            )
            return new_call
        return updated_node
