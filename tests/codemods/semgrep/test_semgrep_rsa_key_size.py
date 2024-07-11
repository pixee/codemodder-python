import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_rsa_key_size import SemgrepRsaKeySize


class TestSemgrepRsaKeySize(BaseSASTCodemodTest):
    codemod = SemgrepRsaKeySize
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "rsa-key-size"

    def _run_and_assert_with_results(self, tmpdir, input_code, expected_output):
        results = {
            "runs": [
                {
                    "results": [
                        {
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 37,
                                            "endLine": 3,
                                            "snippet": {
                                                "text": "rsa.generate_private_key(65537, 1024)"
                                            },
                                            "startColumn": 33,
                                            "startLine": 3,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected an insufficient key size for RSA. NIST recommends a key size of 2048 or higher."
                            },
                            "properties": {},
                            "ruleId": "python.cryptography.security.insufficient-rsa-key-size.insufficient-rsa-key-size",
                        }
                    ]
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected_output,
            results=json.dumps(results),
        )

    def test_keysize_arg(self, tmpdir):
        input_code = """\
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        rsa.generate_private_key(65537, 1024)
        """
        expected_output = """\
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        rsa.generate_private_key(65537, 2048)
        """

        self._run_and_assert_with_results(tmpdir, input_code, expected_output)

    def test_keysize_kwarg(self, tmpdir):
        input_code = """\
        from cryptography.hazmat.primitives.asymmetric import rsa

        rsa.generate_private_key(65537, key_size=1024)
        """
        expected_output = """\
        from cryptography.hazmat.primitives.asymmetric import rsa

        rsa.generate_private_key(65537, key_size=2048)
        """
        self._run_and_assert_with_results(tmpdir, input_code, expected_output)
