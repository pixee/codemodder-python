import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from src.codemods.secure_random import SecureRandom


class TestSecureRandom:
    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                f"""import random

random.random()
var = "hello"
        """,
                """import secrets

secrets.randbits(10)
var = "hello"
        """,
            ),
            (
                f"""from random import random

random()
var = "hello"
            """,
                """import secrets

secrets.randbits(10)
var = "hello"
            """,
            ),
            # other functions in random are not changed
            (
                f"""import random

    random.uniform(1, 2)
            """,
                """import random

    random.uniform(1, 2)
            """,
            ),
            # random import isn't removed if other functions are used
            (
                f"""import random

    random.random()
    random.uniform(1, 2)
            """,
                """import random
import secrets
secrets.randbits(10)
random.uniform(1, 2)
            """,
            ),
            # code leads to error
            (
                f"""random.random()

    import random
            """,
                """random.random()

    import random
            """,
            ),
        ],
    )
    def test_expected_mod(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        command_instance = SecureRandom(CodemodContext())
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output
