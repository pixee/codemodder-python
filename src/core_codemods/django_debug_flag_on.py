import libcst as cst

from codemodder.codemods.utils import is_django_settings_file
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class DjangoDebugFlagOn(SimpleCodemod):
    metadata = Metadata(
        name="django-debug-flag-on",
        summary="Disable Django Debug Mode",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure"
            ),
            Reference(
                url="https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-DEBUG"
            ),
        ],
    )
    change_description = "Flip `Django` debug flag to off."
    detector_pattern = """
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
