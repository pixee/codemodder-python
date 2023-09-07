import pytest
from codemodder.codemods.jwt_decode_verify import JwtDecodeVerify
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestJwtDecodeVerify(BaseSemgrepCodemodTest):
    codemod = JwtDecodeVerify

    def test_rule_ids(self):
        assert self.codemod.RULE_IDS == ["jwt-decode-verify"]

    def test_import(self, tmpdir):
        input_code = """import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)
var = "hello"
"""
        expexted_output = """import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_from_import(self, tmpdir):
        input_code = """from jwt import decode

decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)
var = "hello"
"""
        expexted_output = """from jwt import decode

decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_alias(self, tmpdir):
        input_code = """import jwt as _jwtmod

_jwtmod.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=False)
var = "hello"
"""
        expexted_output = """import jwt as _jwtmod

_jwtmod.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

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
        ],
    )
    def test_verify_variations(self, tmpdir, input_args, expected_args):
        input_code = f"""import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], {input_args})
var = "hello"
"""
        expexted_output = f"""import jwt

jwt.decode(encoded_jwt, SECRET_KEY, algorithms=['HS256'], {expected_args})
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_multiline_formatting_verify_flag(self, tmpdir):
        input_code = """import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=False
)
var = "hello"
"""
        expexted_output = """import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"], verify=True)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.skip(reason="Cannot support multiline opts dict given pattern-regex")
    def test_multiline_formatting_options(self, tmpdir):
        input_code = """import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"],
    options={"verify_signature": False, "verify_exp": False}
)
var = "hello"
"""
        expexted_output = """import jwt

decoded_payload = jwt.decode(
    encoded_jwt, SECRET_KEY, algorithms=["HS256"],
    options={"verify_signature": True, "verify_exp": True}
)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)
