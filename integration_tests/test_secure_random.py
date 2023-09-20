from core_codemods.secure_random import SecureRandom
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestSecureRandom(BaseIntegrationTest):
    codemod = SecureRandom
    code_path = "tests/samples/insecure_random.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (0, """import secrets\n\n"""),
            (1, ""),
            (2, """secrets.SystemRandom().random()\n"""),
        ],
    )

    expected_diff = '--- \n+++ \n@@ -1,4 +1,4 @@\n-import random\n+import secrets\n \n-random.random()\n+secrets.SystemRandom().random()\n var = "hello"\n'
    expected_line_change = "3"
    change_description = SecureRandom.CHANGE_DESCRIPTION
