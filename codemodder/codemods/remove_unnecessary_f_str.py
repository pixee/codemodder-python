import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.commands.unnecessary_format_string import UnnecessaryFormatString
from libcst.metadata import PositionProvider
from codemodder.codemods.change import Change
import libcst.matchers as m
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.file_context import FileContext


class RemoveUnnecessaryFStr(BaseCodemod, UnnecessaryFormatString):
    METADATA = CodemodMetadata(
        DESCRIPTION=UnnecessaryFormatString.DESCRIPTION,
        NAME="remove-unnecessary-f-str",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    CHANGE_DESCRIPTION = UnnecessaryFormatString.DESCRIPTION

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        UnnecessaryFormatString.__init__(self, codemod_context)
        BaseCodemod.__init__(self, file_context)

    @m.leave(m.FormattedString(parts=(m.FormattedStringText(),)))
    def _check_formatted_string(
        self,
        _original_node: cst.FormattedString,
        updated_node: cst.FormattedString,
    ):
        transformed_node = super()._check_formatted_string(_original_node, updated_node)
        if not _original_node.deep_equals(transformed_node):
            line_number = self.lineno_for_node(_original_node)
            self.CHANGES_IN_FILE.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )
        return transformed_node
