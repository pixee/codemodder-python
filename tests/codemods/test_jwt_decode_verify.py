import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.jwt_decode_verify import JwtDecodeVerify


class TestJwtDecodeVerify(BaseCodemodTest):
    codemod = JwtDecodeVerify

    def test_name(self):
        assert self.codemod.name == "jwt-decode-verify"

    def test_import(self, tmpdir):
        input_code = """import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)
var = "hello"
"""
        expected_output = """import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_from_import(self, tmpdir):
        input_code = """from jwt import decode

decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)
var = "hello"
"""
        expected_output = """from jwt import decode

decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_alias(self, tmpdir):
        input_code = """import jwt as _jwtmod

_jwtmod.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)
var = "hello"
"""
        expected_output = """import jwt as _jwtmod

_jwtmod.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_args,expected_args",
        [
            (
                "",
                "",
            ),
            (
                "verify=True",
                "verify=True",
            ),
            (
                """verify=False, options={"verify_signature": False}""",
                """verify=True, options={"verify_signature": True}""",
            ),
            (
                """options={"verify_exp": False}""",
                """options={"verify_exp": True}""",
            ),
            (
                """options={"verify_iss": False, "verify_exp": False, }""",
                """options={"verify_iss": True, "verify_exp": True}""",
            ),
            (
                """options={"strict_aud": False, "verify_signature": False}""",
                """options={"strict_aud": False, "verify_signature": True}""",
            ),
            (
                """options={"verify_iss": True, "verify_signature": True}""",
                """options={"verify_iss": True, "verify_signature": True}""",
            ),
        ],
    )
    def test_verify_variations(self, tmpdir, input_args, expected_args):
        input_code = f"""import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], {input_args})
var = "hello"
"""
        expected_output = f"""import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], {expected_args})
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_multiline_formatting_verify_flag(self, tmpdir):
        input_code = """import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False
)
var = "hello"
"""
        expected_output = """import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("quote", ["'", '"'])
    def test_multiline_formatting_options(self, tmpdir, quote):
        input_code = f"""import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"],
    options={{{quote}verify_signature{quote}: False, {quote}verify_exp{quote}: False}}
)
var = "hello"
"""
        expected_output = f"""import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"],
    options={{{quote}verify_signature{quote}: True, {quote}verify_exp{quote}: True}})
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)
