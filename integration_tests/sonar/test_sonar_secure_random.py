from codemodder.codemods.test.integration_utils import SonarRemediationIntegrationTest
from core_codemods.secure_random import SecureRandomTransformer
from core_codemods.sonar.sonar_secure_random import SonarSecureRandom


class TestSonarSecureRandom(SonarRemediationIntegrationTest):
    codemod = SonarSecureRandom
    code_path = "tests/samples/secure_random.py"
    expected_diff_per_change = [
        "--- \n+++ \n@@ -1,4 +1,5 @@\n import random\n+import secrets\n \n-random.random()\n+secrets.SystemRandom().random()\n random.getrandbits(1)\n",
        "--- \n+++ \n@@ -1,4 +1,5 @@\n import random\n+import secrets\n \n random.random()\n-random.getrandbits(1)\n+secrets.SystemRandom().getrandbits(1)\n",
    ]

    expected_lines_changed = [3, 4]
    change_description = SecureRandomTransformer.change_description
    num_changes = 2
