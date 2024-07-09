import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_jwt_decode_verify import SemgrepJwtDecodeVerify


class TestSemgrepJwtDecodeVerify(BaseSASTCodemodTest):
    codemod = SemgrepJwtDecodeVerify
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "jwt-decode-verify"

    def test_import(self, tmpdir):
        input_code = """
        import jwt

        jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'],  options={"verify_signature": False})
        """
        expected_output = """
        import jwt

        jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'],  options={"verify_signature": True})
        """
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
                                            "endColumn": 93,
                                            "endLine": 4,
                                            "snippet": {
                                                "text": "jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], options={\"verify_signature\": False})"
                                            },
                                            "startColumn": 88,
                                            "startLine": 4,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected JWT token decoded with 'verify=False'. This bypasses any integrity checks for the token which means the token could be tampered with by malicious actors. Ensure that the JWT token is verified."
                            },
                            "ruleId": "python.jwt.security.unverified-jwt-decode.unverified-jwt-decode",
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
