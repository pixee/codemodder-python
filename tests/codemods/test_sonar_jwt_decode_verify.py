import json
from core_codemods.sonar.sonar_jwt_decode_verify import SonarJwtDecodeVerify
from codemodder.codemods.test import BaseSASTCodemodTest


class TestSonarJwtDecodeVerify(BaseSASTCodemodTest):
    codemod = SonarJwtDecodeVerify
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "jwt-decode-verify-S5659"

    def test_simple(self, tmpdir):
        input_code = """
        import jwt

        SECRET_KEY = "mysecretkey"
        payload = {
            "user_id": 123,
            "username": "john",
        }

        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)
        """
        expected = """
        import jwt

        SECRET_KEY = "mysecretkey"
        payload = {
            "user_id": 123,
            "username": "john",
        }

        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": f"{tmpdir / 'code.py'}",
                    "textRange": {
                        "startLine": 11,
                        "endLine": 11,
                        "startOffset": 76,
                        "endOffset": 88,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
