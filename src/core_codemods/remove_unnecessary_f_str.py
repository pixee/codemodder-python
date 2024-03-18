from typing import cast

import libcst as cst
import libcst.matchers as m
from libcst.codemod.commands.unnecessary_format_string import UnnecessaryFormatString

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class RemoveUnnecessaryFStrTransform(LibcstResultTransformer):
    change_description = "Remove unnecessary f-string"

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

        transformed_node = UnnecessaryFormatString._check_formatted_string(
            cast(UnnecessaryFormatString, self), _original_node, updated_node
        )
        if not _original_node.deep_equals(transformed_node):
            self.report_change(_original_node)
        return transformed_node


RemoveUnnecessaryFStr = CoreCodemod(
    metadata=Metadata(
        name="remove-unnecessary-f-str",
        summary="Remove Unnecessary F-strings",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://pylint.readthedocs.io/en/latest/user_guide/messages/warning/f-string-without-interpolation.html"
            ),
            Reference(
                url="https://github.com/Instagram/LibCST/blob/main/libcst/codemod/commands/unnecessary_format_string.py"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(RemoveUnnecessaryFStrTransform),
    detector=None,
)
