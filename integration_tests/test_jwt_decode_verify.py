from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.jwt_decode_verify import JwtDecodeVerify, JwtDecodeVerifyTransformer


class TestJwtDecodeVerify(BaseIntegrationTest):
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
    change_description = JwtDecodeVerifyTransformer.change_description
