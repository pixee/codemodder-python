from core_codemods.django_debug_flag_on import DjangoDebugFlagOn
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestDjangoDebugFlagFlip(BaseIntegrationTest):
    codemod = DjangoDebugFlagOn
    code_path = "tests/samples/django-project/mysite/mysite/settings.py"

    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(25, "DEBUG = False\n")]
    )
    expected_diff = '--- \n+++ \n@@ -23,7 +23,7 @@\n SECRET_KEY = "django-insecure-t*rrda&qd4^#q+50^%q^rrsp-t$##&u5_#=9)&@ei^ppl6$*c*"\n \n # SECURITY WARNING: don\'t run with debug turned on in production!\n-DEBUG = True\n+DEBUG = False\n \n ALLOWED_HOSTS = []\n \n'
    expected_line_change = "26"
    change_description = DjangoDebugFlagOn.CHANGE_DESCRIPTION
