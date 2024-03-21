from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.django_debug_flag_on import DjangoDebugFlagOn


class TestDjangoDebugFlagFlip(BaseIntegrationTest):
    codemod = DjangoDebugFlagOn
    code_filename = "settings.py"
    original_code = """
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True
    """
    replacement_lines = [(2, "DEBUG = False\n")]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -1,2 +1,2 @@\n"""
    """ # SECURITY WARNING: don't run with debug turned on in production!\n"""
    """-DEBUG = True\n"""
    """+DEBUG = False\n"""
    )
    # fmt: on
    expected_line_change = "2"
    change_description = DjangoDebugFlagOn.change_description
