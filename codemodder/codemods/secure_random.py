import libcst as cst
from libcst.codemod import (
    CodemodContext,
)
from typing import List

from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from codemodder.codemods.change import Change
from codemodder.codemods.base_codemod import (
    CodemodMetadata,
    ReviewGuidance,
    SemgrepCodemod,
)
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.utils import get_call_name
from codemodder.file_context import FileContext


system_random_object_name = "gen"


class SecureRandom(SemgrepCodemod, BaseTransformer):
    METADATA = CodemodMetadata(
        DESCRIPTION="Replaces random.{func} with more secure secrets library functions.",
        NAME="secure-random",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    YAML_FILES = [
        "secure_random.yaml",
    ]
    CHANGE_DESCRIPTION = "Switch use of random module functions secrets.SystemRandom()"
    CHANGES_IN_FILE: List = []

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
            AddImportsVisitor.add_needed_import(self.context, "secrets")
            RemoveImportsVisitor.remove_unused_import_by_node(
                self.context, original_node
            )
            new_call = cst.Call(
                func=cst.Attribute(
                    value=cst.parse_expression("secrets.SystemRandom()"),
                    attr=cst.Name(value=get_call_name(original_node)),
                ),
                args=original_node.args,
            )
            return new_call
        return updated_node
