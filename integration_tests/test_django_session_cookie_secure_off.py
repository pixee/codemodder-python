from core_codemods.django_session_cookie_secure_off import (
    DjangoSessionCookieSecureOff,
)
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestDjangoSessionCookieSecureOff(BaseIntegrationTest):
    codemod = DjangoSessionCookieSecureOff
    code_path = "tests/samples/django-project/mysite/mysite/settings.py"

    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(124, "SESSION_COOKIE_SECURE = True\n")]
    )
    expected_diff = '--- \n+++ \n@@ -121,3 +121,4 @@\n # https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field\n \n DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"\n+SESSION_COOKIE_SECURE = True\n'
    expected_line_change = "124"
    change_description = DjangoSessionCookieSecureOff.CHANGE_DESCRIPTION
