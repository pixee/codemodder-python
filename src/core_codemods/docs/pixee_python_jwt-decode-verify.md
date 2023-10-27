This codemod ensures calls to [jwt.decode](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode) do not disable signature validation and other verifications. It checks that both the `verify` parameter (soon to be deprecated) and any `verify` key in the `options` dict parameter are not assigned to `False`.

Our change looks as follows:

```diff
  import jwt
  ...
- decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False)
+ decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)
  ...
- decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False, "verify_exp": False})
+ decoded_payload = jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"], options={"verify_signature": True, "verify_exp": True})
```

Any `verify` parameter not listed relies on the secure `True` default value.
