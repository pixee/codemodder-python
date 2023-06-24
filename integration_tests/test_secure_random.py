from codemodder.codemods.secure_random import SecureRandom, RandomVisitor
from integration_tests.base_test import BaseIntegrationTest


class TestSecureRandom(BaseIntegrationTest):
    codemod = SecureRandom
    code_path = "tests/samples/insecure_random.py"
    original_code = 'import random\n\nrandom.random()\nvar = "hello"\n'
    expected_new_code = 'import secrets\ngen = secrets.SystemRandom()\n\ngen.uniform(0, 1)\nvar = "hello"\n'
    expected_diff = '--- \n+++ \n@@ -1,4 +1,5 @@\n-import random\n+import secrets\n+gen = secrets.SystemRandom()\n \n-random.random()\n+gen.uniform(0, 1)\n var = "hello"\n'
    expected_line_change = "3"
    change_description = RandomVisitor.CHANGE_DESCRIPTION
