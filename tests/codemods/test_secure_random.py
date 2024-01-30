import pytest
from core_codemods.secure_random import SecureRandom
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestSecureRandom(BaseSemgrepCodemodTest):
    codemod = SecureRandom

    def test_name(self):
        assert self.codemod.name() == "secure-random"

    def test_import_random(self, tmpdir):
        input_code = """import random

random.random()
var = "hello"
"""
        expected_output = """import secrets

secrets.SystemRandom().random()
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_from_random(self, tmpdir):
        input_code = """from random import random

random()
var = "hello"
"""
        expected_output = """import secrets

secrets.SystemRandom().random()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_alias(self, tmpdir):
        input_code = """import random as alleatory

alleatory.random()
var = "hello"
"""
        expected_output = """import secrets

secrets.SystemRandom().random()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """import random

random.randint(0, 10)
var = "hello"
""",
                """import secrets

secrets.SystemRandom().randint(0, 10)
var = "hello"
""",
            ),
            (
                """from random import randint

randint(0, 10)
var = "hello"
""",
                """import secrets

secrets.SystemRandom().randint(0, 10)
var = "hello"
""",
            ),
        ],
    )
    def test_random_randint(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_multiple_calls(self, tmpdir):
        input_code = """import random

random.random()
random.randint()
var = "hello"
"""
        expected_output = """import secrets

secrets.SystemRandom().random()
secrets.SystemRandom().randint()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """import random
import csv
random.random()
csv.excel
""",
                """import csv
import secrets

secrets.SystemRandom().random()
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

secrets.SystemRandom().random()
excel
""",
            ),
        ],
    )
    def test_random_other_import_untouched(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_nameerror(self, tmpdir):
        input_code = """random.random()

import random"""
        expected_output = input_code
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_multifunctions(self, tmpdir):
        # Test that `random` import isn't removed if code uses part of the random
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """import random

random.random()
random.__all__
"""

        expected_output = """import random
import secrets

secrets.SystemRandom().random()
random.__all__
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_systemrandom(self, tmpdir):
        input_code = """
        import random

        rand = random.SystemRandom()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_random_systemrandom_importfrom(self, tmpdir):
        input_code = """
        from random import SystemRandom

        rand = SystemRandom()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_random_systemrandom_import_alias(self, tmpdir):
        input_code = """
        import random as domran

        rand = domran.SystemRandom()
        """
        self.run_and_assert(tmpdir, input_code, input_code)
