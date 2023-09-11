from libcst.metadata import PositionProvider, ScopeProvider
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.file_context import FileContext
import libcst as cst
from libcst.codemod import Codemod, CodemodContext


class HTTPSConnection(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Enforce HTTPS connection"),
        NAME="https-connection",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    CHANGE_DESCRIPTION = "Enforced HTTPS connection"

    METADATA_DEPENDENCIES = (PositionProvider, ScopeProvider)

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, file_context)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree

    def filter_by_path_includes_or_excludes(self, pos_to_match):
        """
        Returns False if the node, whose position in the file is pos_to_match, matches any of the lines specified in the path-includes or path-excludes flags.
        """
        # excludes takes precedence if defined
        if self.line_exclude:
            return not any(match_line(pos_to_match, line) for line in self.line_exclude)
        if self.line_include:
            return any(match_line(pos_to_match, line) for line in self.line_include)
        return True

    def node_position(self, node):
        # See https://github.com/Instagram/LibCST/blob/main/libcst/_metadata_dependent.py#L112
        return self.get_metadata(PositionProvider, node)


def match_line(pos, line):
    return pos.start.line == line and pos.end.line == line
