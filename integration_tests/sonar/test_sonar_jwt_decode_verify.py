from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_jwt_decode_verify import (
    JwtDecodeVerifySASTTransformer,
    SonarJwtDecodeVerify,
)


class TestJwtDecodeVerify(SonarIntegrationTest):
    codemod = SonarJwtDecodeVerify
    code_path = "tests/samples/jwt_decode_verify.py"
    replacement_lines = [
        (
            11,
            """decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n""",
        ),
        (
            12,
            """decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})\n""",
        ),
    ]

    expected_diff = '--- \n+++ \n@@ -8,7 +8,7 @@\n \n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")\n \n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})\n \n var = "something"\n'
    expected_line_change = "11"
    num_changes = 2
    change_description = JwtDecodeVerifySASTTransformer.change_description
