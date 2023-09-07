import jwt

SECRET_KEY = "mysecretkey"
payload = {
    "user_id": 123,
    "username": "john",
}

encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# these will work without black formatting
decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)
decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})

# these will not work with semgrep pattern-regex
decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False
)
decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False}
)
var = "something"
