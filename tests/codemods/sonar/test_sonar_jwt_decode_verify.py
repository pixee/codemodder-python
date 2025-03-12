import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_jwt_decode_verify import SonarJwtDecodeVerify


class TestSonarJwtDecodeVerify(BaseSASTCodemodTest):
    codemod = SonarJwtDecodeVerify
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "jwt-decode-verify"

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
        decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})
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
        decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})
        """

        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -8,5 +8,5 @@
 }
 
 encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)
+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)
 decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})
""",
            """\
--- 
+++ 
@@ -9,4 +9,4 @@
 
 encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
 decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)
-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})
+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})
""",
        ]

        issues = {
            "issues": [
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 11,
                        "endLine": 11,
                        "startOffset": 76,
                        "endOffset": 88,
                    },
                },
                {
                    "rule": "python:S5659",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 12,
                        "endLine": 12,
                        "startOffset": 84,
                        "endOffset": 111,
                    },
                },
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            expected_diff_per_change,
            results=json.dumps(issues),
            num_changes=2,
        )
