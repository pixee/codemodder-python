import libcst as cst
from libcst.codemod import (
    CodemodContext,
)
from libcst.codemod.commands.unnecessary_format_string import UnnecessaryFormatString
import libcst.matchers as m
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import BaseCodemod


class RemoveUnnecessaryFStr(BaseCodemod, UnnecessaryFormatString):
    NAME = "remove-unnecessary-f-str"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Remove Unnecessary F-strings"
    DESCRIPTION = UnnecessaryFormatString.DESCRIPTION
    REFERENCES = [
        {
            "url": "https://pylint.readthedocs.io/en/latest/user_guide/messages/warning/f-string-without-interpolation.html",
            "description": "",
        },
        {
            "url": "https://github.com/Instagram/LibCST/blob/main/libcst/codemod/commands/unnecessary_format_string.py",
            "description": "",
        },
    ]

    def __init__(self, codemod_context: CodemodContext, *codemod_args):
        UnnecessaryFormatString.__init__(self, codemod_context)
        BaseCodemod.__init__(self, codemod_context, *codemod_args)

    @m.leave(m.FormattedString(parts=(m.FormattedStringText(),)))
    def _check_formatted_string(
        self,
        _original_node: cst.FormattedString,
        updated_node: cst.FormattedString,
    ):
        if not self.filter_by_path_includes_or_excludes(
            self.node_position(_original_node)
        ):
            return updated_node

        transformed_node = super()._check_formatted_string(_original_node, updated_node)
        if not _original_node.deep_equals(transformed_node):
            self.report_change(_original_node)
        return transformed_node
