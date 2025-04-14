from codemodder.codemods.test.integration_utils import SonarRemediationIntegrationTest
from core_codemods.sonar.sonar_jwt_decode_verify import (
    JwtDecodeVerifySASTTransformer,
    SonarJwtDecodeVerify,
)


class TestJwtDecodeVerify(SonarRemediationIntegrationTest):
    codemod = SonarJwtDecodeVerify
    code_path = "tests/samples/jwt_decode_verify.py"

    expected_diff_per_change = [
        '--- \n+++ \n@@ -8,7 +8,7 @@\n \n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")\n \n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})\n \n var = "something"\n',
        '--- \n+++ \n@@ -9,6 +9,6 @@\n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")\n \n decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})\n \n var = "something"\n',
    ]

    expected_lines_changed = [11, 12]
    num_changes = 2
    change_description = JwtDecodeVerifySASTTransformer.change_description
