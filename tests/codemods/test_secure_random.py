import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from src.codemods.secure_random import SecureRandom


class TestSecureRandom:
    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                """import random

random.random()
var = "hello"

        """,
                """import secrets

secrets.randbits(10)
var = "hello"

        """,
            ),
            ("truthy", False),
            ("", True),
            (False, True),
            (None, True),
        ],
    )
    def test_expected_mod(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        command_instance = SecureRandom(CodemodContext())
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output
