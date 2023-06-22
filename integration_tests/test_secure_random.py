from codemodder.codemods.secure_random import SecureRandom
from integration_tests.base_test import BaseIntegrationTest


class TestSecureRandom(BaseIntegrationTest):
    codemod = SecureRandom
    code_path = "tests/samples/insecure_random.py"
    original_code = 'import random\n\nrandom.random()\nvar = "hello"\n'
    expected_new_code = 'import secrets\ngen = secrets.SystemRandom()\n\ngen.uniform(0, 1)\nvar = "hello"\n'
