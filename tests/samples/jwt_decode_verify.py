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
