from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.secure_random import SecureRandomTransformer
from core_codemods.sonar.sonar_secure_random import SonarSecureRandom


class TestSonarDjangoJsonResponseType(SonarIntegrationTest):
    codemod = SonarSecureRandom
    code_path = "tests/samples/secure_random.py"
    replacement_lines = [
        (1, """import secrets\n"""),
        (3, """secrets.SystemRandom().random()\n"""),
        (4, """secrets.SystemRandom().getrandbits(1)\n"""),
    ]
    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,4 +1,4 @@\n"""
        """-import random\n"""
        """+import secrets\n"""
        """ \n"""
        """-random.random()\n"""
        """-random.getrandbits(1)\n"""
        """+secrets.SystemRandom().random()\n"""
        """+secrets.SystemRandom().getrandbits(1)\n""")
    # fmt: on
    expected_line_change = "3"
    change_description = SecureRandomTransformer.change_description
    num_changes = 2
