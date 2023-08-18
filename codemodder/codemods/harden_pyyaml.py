import libcst as cst
from libcst.codemod import CodemodContext
import yaml

from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.change import Change
from codemodder.file_context import FileContext


UNSAFE_LOADERS = yaml.loader.__all__.copy()  # type: ignore
UNSAFE_LOADERS.remove("SafeLoader")


class HardenPyyaml(SemgrepCodemod, BaseTransformer):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Ensures all calls to yaml.load use `SafeLoader`."),
        NAME="harden-pyyaml",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    CHANGE_DESCRIPTION = "Ensures all calls to yaml.load use `SafeLoader`."
    YAML_FILES = [
        "harden-pyyaml.yaml",
    ]

    CHANGE_DESCRIPTION = "Adds `yaml.SafeLoader` to yaml.load calls"

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
            second_arg = cst.Arg(value=cst.parse_expression("yaml.SafeLoader"))
            return updated_node.with_changes(args=[*updated_node.args[:1], second_arg])
        return updated_node
