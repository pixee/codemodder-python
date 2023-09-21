from typing import List
import libcst as cst
from libcst.codemod import Codemod, CodemodContext
from libcst.metadata import PositionProvider
from codemodder.change import Change
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.utils import is_django_settings_file
from codemodder.file_context import FileContext


class DjangoSessionCookieSecureOff(SemgrepCodemod, Codemod):
    METADATA = CodemodMetadata(
        DESCRIPTION=("Sets Django's `SESSION_COOKIE_SECURE` flag if off or missing."),
        NAME="django-session-cookie-secure-off",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_REVIEW,
    )
    SUMMARY = "Secure setting for Django `SESSION_COOKIE_SECURE` flag"
    CHANGE_DESCRIPTION = METADATA.DESCRIPTION
    YAML_FILES = [
        "detect-django-settings.yaml",
    ]

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, codemod_context: CodemodContext, *args):
        Codemod.__init__(self, codemod_context)
        SemgrepCodemod.__init__(self, *args)

    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        if is_django_settings_file(self.file_context.file_path):
            transformer = SessionCookieSecureTransformer(
                self.context, self.file_context, self._results
            )
            new_tree = transformer.transform_module(tree)
            if transformer.changes_in_file:
                self.file_context.codemod_changes.extend(transformer.changes_in_file)
            return new_tree
        return tree


class SessionCookieSecureTransformer(BaseTransformer):
    def __init__(
        self, codemod_context: CodemodContext, file_context: FileContext, results
    ):
        super().__init__(codemod_context, results)
        self.line_exclude = file_context.line_exclude
        self.line_include = file_context.line_include
        self.changes_in_file: List[Change] = []
        self.flag_correctly_set = False

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """
        Handle case for `SESSION_COOKIE_SECURE`  is missing from settings.py
        """
        if self.flag_correctly_set or len(self.changes_in_file):
            # Nothing to do at the end of the module if
            # `SESSION_COOKIE_SECURE = True` or if assigned to
            # something else and we changed it in `leave_Assign`.
            return updated_node

        # line_number is the end of the module where we will insert the new flag.
        pos_to_match = self.node_position(original_node)
        line_number = pos_to_match.end.line
        self.changes_in_file.append(
            Change(
                str(line_number), DjangoSessionCookieSecureOff.CHANGE_DESCRIPTION
            ).to_json()
        )
        final_line = cst.parse_statement("SESSION_COOKIE_SECURE = True")
        new_body = updated_node.body + (final_line,)
        return updated_node.with_changes(body=new_body)

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign:
        """
        Handle case for `SESSION_COOKIE_SECURE = not True` in settings.py
        """
        pos_to_match = self.node_position(original_node)
        if is_session_cookie_secure(
            original_node
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            if is_assigned_to_True(original_node):
                self.flag_correctly_set = True
                return updated_node

            # SESSION_COOKIE_SECURE = anything other than True
            line_number = pos_to_match.start.line
            self.changes_in_file.append(
                Change(
                    str(line_number), DjangoSessionCookieSecureOff.CHANGE_DESCRIPTION
                ).to_json()
            )
            return updated_node.with_changes(value=cst.Name("True"))
        return updated_node


def is_session_cookie_secure(original_node: cst.Assign):
    if len(original_node.targets) > 1:
        return False

    target_var = original_node.targets[0].target
    return (
        isinstance(target_var, cst.Name) and target_var.value == "SESSION_COOKIE_SECURE"
    )


def is_assigned_to_True(original_node: cst.Assign):
    return (
        isinstance(original_node.value, cst.Name)
        and original_node.value.value == "True"
    )
