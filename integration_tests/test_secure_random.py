from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.secure_random import SecureRandom, SecureRandomTransformer


class TestSecureRandom(BaseIntegrationTest):
    codemod = SecureRandom
    original_code = """
    import random
    random.random()
    var = "hello"
    """
    replacement_lines = [
        (1, """import secrets\n\n"""),
        (2, """secrets.SystemRandom().random()\n"""),
    ]
    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,3 +1,4 @@\n"""
        """-import random\n"""
        """-random.random()\n"""
        """+import secrets\n"""
        """+\n"""
        """+secrets.SystemRandom().random()\n"""
        """ var = "hello"\n""")
    # fmt: on
    expected_line_change = "2"
    change_description = SecureRandomTransformer.change_description
