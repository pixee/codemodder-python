import libcst as cst
from libcst.codemod import CodemodContext
from libcst import matchers
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.change import Change
from codemodder.file_context import FileContext


class HardenRuamel(SemgrepCodemod, BaseTransformer):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Ensures all unsafe calls to ruamel.yaml.YAML use `typ='safe'`."),
        NAME="harden-ruamel",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    CHANGE_DESCRIPTION = METADATA.DESCRIPTION
    YAML_FILES = [
        "harden-ruamel.yaml",
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

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            self.CHANGES_IN_FILE.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )
            new_args = update_arg_target(original_node.args, target_arg="typ")
            return updated_node.with_changes(args=new_args)
        return updated_node


def update_arg_target(original_args, target_arg):
    new_args = []
    for arg in original_args:
        if matchers.matches(arg.keyword, matchers.Name(target_arg)):
            new = cst.Arg(
                keyword=cst.parse_expression("typ"),
                value=cst.parse_expression('"safe"'),
                equal=arg.equal,
            )
        else:
            new = arg
        new_args.append(new)
    return new_args
