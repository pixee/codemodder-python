import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_secure_random import SonarSecureRandom


class TestSonarSecureRandom(BaseSASTCodemodTest):
    codemod = SonarSecureRandom
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "secure-random"

    def test_simple(self, tmpdir):
        input_code = """
        import random

        random.getrandbits(1)
        random.randint(0, 9)
        random.random()
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().getrandbits(1)
        secrets.SystemRandom().randint(0, 9)
        secrets.SystemRandom().random()
        """
        hotspots = {
            "hotspots": [
                {
                    "rule": "python:S2245",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 4,
                        "endLine": 4,
                        "startOffset": 0,
                        "endOffset": 21,
                    },
                },
                {
                    "rule": "python:S2245",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 5,
                        "endLine": 5,
                        "startOffset": 0,
                        "endOffset": 20,
                    },
                },
                {
                    "rule": "python:S2245",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 6,
                        "endLine": 6,
                        "startOffset": 0,
                        "endOffset": 15,
                    },
                },
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(hotspots),
            num_changes=3,
        )
