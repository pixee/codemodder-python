import libcst as cst
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.utils import is_django_settings_file


class DjangoDebugFlagOn(SemgrepCodemod):
    NAME = "django-debug-flag-on"
    DESCRIPTION = "Flip `Django` debug flag to off."
    SUMMARY = "Disable Django Debug Mode"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW
    REFERENCES = [
        {
            "url": "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
            "description": "",
        },
        {
            "url": "https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-DEBUG",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - id: django-debug-flag-on
            pattern: DEBUG = True
            paths:
              include:
               - settings.py
        """

    def visit_Module(self, _: cst.Module) -> bool:
        """
        Only visit module with this codemod if it's a settings.py file.
        """
        return is_django_settings_file(self.file_context.file_path)

    def on_result_found(self, _, updated_node):
        return updated_node.with_changes(value=cst.Name("False"))
