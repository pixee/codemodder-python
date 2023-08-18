import libcst as cst
from libcst.codemod import CodemodContext

from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.change import Change
from codemodder.file_context import FileContext


default_limit = "5_000_000"


class LimitReadline(SemgrepCodemod, BaseTransformer):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Adds a size limit argument to readline() calls."),
        NAME="limit-readline",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
    )
    CHANGE_DESCRIPTION = "Adds a size limit argument to readline() calls."
    YAML_FILES = [
        "limit-readline.yaml",
    ]

    CHANGE_DESCRIPTION = "Adds a size limit argument to readline() calls."

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        SemgrepCodemod.__init__(self, file_context)
        BaseTransformer.__init__(
            self,
            codemod_context,
            self._results,
            file_context.line_exclude,
            file_context.line_include,
        )

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            self.CHANGES_IN_FILE.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )
            return updated_node.with_changes(args=[cst.Arg(cst.Integer(default_limit))])
        return updated_node
