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
                9,
                """decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)\n""",
            ),
            (
                10,
                """decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], options={"verify_signature": True})\n""",
            ),
        ],
    )
    expected_diff = "--- \n+++ \n@@ -7,6 +7,6 @@\n }\n \n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm='HS256')\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], options={\"verify_signature\": False})\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], options={\"verify_signature\": True})\n var = \"something\""
    expected_line_change = "10"
    num_changes = 2
    change_description = JwtDecodeVerify.CHANGE_DESCRIPTION
