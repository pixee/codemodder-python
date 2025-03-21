from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from core_codemods.jwt_decode_verify import JwtDecodeVerify, JwtDecodeVerifyTransformer


class TestJwtDecodeVerify(BaseRemediationIntegrationTest):
    codemod = JwtDecodeVerify
    original_code = """
    import jwt
    
    SECRET_KEY = "mysecretkey"
    payload = {
        "user_id": 123,
        "username": "john",
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)
    decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})
    
    var = "something"
    """
    expected_diff_per_change = [
        '--- \n+++ \n@@ -8,7 +8,7 @@\n \n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")\n \n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)\n decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})\n \n var = "something"',
        '--- \n+++ \n@@ -9,6 +9,6 @@\n encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")\n \n decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)\n-decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})\n+decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True})\n \n var = "something"',
    ]

    expected_lines_changed = [11, 12]
    num_changes = 2
    change_description = JwtDecodeVerifyTransformer.change_description
