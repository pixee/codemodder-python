from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.django_session_cookie_secure_off import DjangoSessionCookieSecureOff


class TestDjangoSessionCookieSecureOff(BaseIntegrationTest):
    codemod = DjangoSessionCookieSecureOff
    code_filename = "settings.py"

    original_code = """
    # django settings
    # SESSION_COOKIE_SECURE is not defined
    """
    replacement_lines = [(3, "SESSION_COOKIE_SECURE = True\n")]

    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,2 +1,3 @@\n"""
        """ # django settings\n"""
        """ # SESSION_COOKIE_SECURE is not defined\n"""
        """+SESSION_COOKIE_SECURE = True\n"""
    )
    # fmt: on
    expected_line_change = "3"
    change_description = DjangoSessionCookieSecureOff.change_description
