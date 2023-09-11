from typing import List
import libcst as cst
from libcst.codemod import Codemod, CodemodContext
from libcst.metadata import PositionProvider
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.change import Change
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.file_context import FileContext
from codemodder.codemods.utils import is_django_settings_file


class DjangoDebugFlagOn(SemgrepCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Flips django's debug flag if on."),
        NAME="django-debug-flag-on",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
    )
    SUMMARY = CHANGE_DESCRIPTION = "Flips django's debug flag to off."
    YAML_FILES = [
        "django-debug-flag-on.yaml",
    ]

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        Codemod.__init__(self, codemod_context)
        SemgrepCodemod.__init__(self, file_context)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        # checks if the file we looking is a settings.py file from django's default directory structure
        if is_django_settings_file(self.file_context.file_path):
            debug_flag_transformer = DebugFlagTransformer(
                self.context, self.file_context, self._results
            )
            new_tree = debug_flag_transformer.transform_module(tree)
            if debug_flag_transformer.changes_in_file:
                self.file_context.codemod_changes.extend(
                    debug_flag_transformer.changes_in_file
                )
                return new_tree
        return tree


class DebugFlagTransformer(BaseTransformer):
    def __init__(
        self, codemod_context: CodemodContext, file_context: FileContext, results
    ):
        super().__init__(
            codemod_context,
            results,
            file_context.line_exclude,
            file_context.line_include,
        )
        self.changes_in_file: List[Change] = []

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign:
        pos_to_match = self.node_position(original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            self.changes_in_file.append(
                Change(str(line_number), DjangoDebugFlagOn.CHANGE_DESCRIPTION).to_json()
            )
            return updated_node.with_changes(value=cst.Name("False"))
        return updated_node
