from codemodder.codemods.jwt_decode_verify import JwtDecodeVerify
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestJwtDecodeVerify(BaseIntegrationTest):
    codemod = JwtDecodeVerify
    code_path = "tests/samples/jwt_decode_verify.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (
                11,
                """decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n""",
            ),
            (
                12,
                """decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})\n""",
            ),
            (
                16,
                """    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)""",
            ),
            (
                17,
                "\n",
            ),
        ],
    )
    expected_diff = '--- \n+++ \n@@ -9,13 +9,12 @@\n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")\n \n # these will work without black formatting\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})\n \n # these will not work with semgrep pattern-regex\n decoded_payload = jwt.decode(\n-    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False\n-)\n+    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n decoded_payload = jwt.decode(\n     encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False}\n )\n'
    expected_line_change = "12"
    num_changes = 3
    change_description = JwtDecodeVerify.CHANGE_DESCRIPTION
