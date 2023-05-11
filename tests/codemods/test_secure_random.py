import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.secure_random import SecureRandom


class TestSecureRandom:
    def run_and_assert(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        command_instance = SecureRandom(CodemodContext())
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output

    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                f"""import random

random.random()
var = "hello"
        """,
                """import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
var = "hello"
        """,
            ),
            (
                f"""from random import random

random()
var = "hello"
            """,
                """import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
var = "hello"
            """,
            ),
        ],
    )
    def test_random_random(self, input_code, expexted_output):
        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                f"""import random

random.randint(0, 10)
var = "hello"
""",
                """import secrets

gen = secrets.SystemRandom()
gen.randint(0, 10)
var = "hello"
""",
            ),
            (
                f"""from random import randint

randint(0, 10)
var = "hello"
""",
                """import secrets

gen = secrets.SystemRandom()
gen.randint(0, 10)
var = "hello"
""",
            ),
        ],
    )
    def test_random_randint(self, input_code, expexted_output):
        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.skip()
    def test_random_nameerror(self):
        input_code = f"""random.random()

import random
            """
        expexted_output = input_code
        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.skip()
    def test_random_multifunctions(self):
        # Test that `random` import isn't removed if code uses part of the random
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = f"""import random

random.random()
random.__all__
        """

        expexted_output = """import random
import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
random.__all__
    """

        self.run_and_assert(input_code, expexted_output)
