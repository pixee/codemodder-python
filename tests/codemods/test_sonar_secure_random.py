import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_secure_random import SonarSecureRandom


class TestSonarSecureRandom(BaseSASTCodemodTest):
    codemod = SonarSecureRandom
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "secure-random-S2245"

    def test_simple(self, tmpdir):
        input_code = """
        import random

        random.getrandbits(1)
        random.randint(0, 9)
        random.random()
        random.sample(["a", "b"], 1)
        random.choice(["a", "b"])
        random.choices(["a", "b"])
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().getrandbits(1)
        secrets.SystemRandom().randint(0, 9)
        secrets.SystemRandom().random()
        secrets.SystemRandom().sample(["a", "b"], 1)
        secrets.choice(["a", "b"])
        secrets.SystemRandom().choices(["a", "b"])
        """
        # todo: not issues, notspots
        issues = {
            "issues": [
                {
                    "rule": "python:S5905",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 2,
                        "endLine": 2,
                        "startOffset": 8,
                        "endOffset": 15,
                    },
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(issues),
            num_changes=3,
        )
