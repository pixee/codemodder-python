import libcst as cst
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.utils import is_django_settings_file, is_assigned_to_True


class DjangoSessionCookieSecureOff(SemgrepCodemod):
    NAME = "django-session-cookie-secure-off"
    DESCRIPTION = "Sets Django's `SESSION_COOKIE_SECURE` flag if off or missing."
    SUMMARY = "Secure Setting for Django `SESSION_COOKIE_SECURE` flag"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    REFERENCES = [
        {
            "url": "https://owasp.org/www-community/controls/SecureCookieAttribute",
            "description": "",
        },
        {
            "url": "https://docs.djangoproject.com/en/4.2/ref/settings/#session-cookie-secure",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - id: django-session-cookie-secure-off
            # This pattern creates one finding with no text for settings.py file.
            pattern-regex: ^
            paths:
              include:
               - settings.py
        """

    def __init__(self, *args):
        super().__init__(*args)
        self.is_django_settings_file = is_django_settings_file(
            self.file_context.file_path
        )
        self.flag_correctly_set = False

    def visit_Module(self, _: cst.Module) -> bool:
        """
        Only visit module with this codemod if it's a settings.py file.
        """
        return self.is_django_settings_file

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """
        Handle case for `SESSION_COOKIE_SECURE`  is missing from settings.py
        """
        if not self.is_django_settings_file:
            return updated_node

        if self.flag_correctly_set or len(self.file_context.codemod_changes):
            # Nothing to do at the end of the module if
            # `SESSION_COOKIE_SECURE = True` or if assigned to
            # something else and we changed it in `leave_Assign`.
            return updated_node

        self.add_change(original_node, self.CHANGE_DESCRIPTION, start=False)
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
            self.add_change(original_node, self.CHANGE_DESCRIPTION)
            return updated_node.with_changes(value=cst.Name("True"))
        return updated_node


def is_session_cookie_secure(original_node: cst.Assign):
    if len(original_node.targets) > 1:
        return False

    target_var = original_node.targets[0].target
    return (
        isinstance(target_var, cst.Name) and target_var.value == "SESSION_COOKIE_SECURE"
    )
