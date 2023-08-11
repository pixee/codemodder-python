import pytest
from codemodder.codemods.secure_random import SecureRandom
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestSecureRandom(BaseSemgrepCodemodTest):
    codemod = SecureRandom

    def test_rule_ids(self):
        assert self.codemod.RULE_IDS == ["secure-random"]

    def test_import_random(self, tmpdir):
        input_code = """import random

random.random()
var = "hello"
"""
        expexted_output = """import secrets

gen = secrets.SystemRandom()

gen.uniform(0, 1)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.skip()
    def test_from_random(self, tmpdir):
        input_code = """from random import random

random()
var = "hello"
"""
        expexted_output = """import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                """import random

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
                """from random import randint

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
    @pytest.mark.skip()
    def test_random_randint(self, tmpdir, input_code, expexted_output):
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize(
        "input_code,expexted_output",
        [
            (
                """import random
import csv
random.random()
csv.excel
""",
                """import csv
import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
csv.excel
""",
            ),
            (
                """import random
from csv import excel
random.random()
excel
""",
                """from csv import excel
import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
excel
""",
            ),
        ],
    )
    def test_random_other_import_untouched(self, tmpdir, input_code, expexted_output):
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_random_nameerror(self, tmpdir):
        input_code = """random.random()

import random"""
        expexted_output = input_code
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_random_multifunctions(self, tmpdir):
        # Test that `random` import isn't removed if code uses part of the random
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """import random

random.random()
random.__all__
"""

        expexted_output = """import random
import secrets

gen = secrets.SystemRandom()

gen.uniform(0, 1)
random.__all__
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)
