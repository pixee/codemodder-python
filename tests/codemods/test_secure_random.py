import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.secure_random import SecureRandom


class TestSecureRandom(BaseCodemodTest):
    codemod = SecureRandom

    def test_name(self):
        assert self.codemod.name == "secure-random"

    def test_import_random(self, tmpdir):
        input_code = """
        import random

        random.random()
        random.getrandbits(1)
        var = "hello"
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().random()
        secrets.SystemRandom().getrandbits(1)
        var = "hello"
        """

        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_from_random(self, tmpdir):
        input_code = """
        from random import random

        random()
        var = "hello"
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().random()
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_alias(self, tmpdir):
        input_code = """
        import random as alleatory

        alleatory.random()
        var = "hello"
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().random()
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import random

                random.randint(0, 10)
                var = "hello"
                """,
                """
                import secrets

                secrets.SystemRandom().randint(0, 10)
                var = "hello"
                """,
            ),
            (
                """
                from random import randint

                randint(0, 10)
                var = "hello"
                """,
                """
                import secrets

                secrets.SystemRandom().randint(0, 10)
                var = "hello"
                """,
            ),
        ],
    )
    def test_random_randint(self, tmpdir, input_code, expected_output):
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_multiple_calls(self, tmpdir):
        input_code = """
        import random

        random.random()
        random.randint()
        var = "hello"
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().random()
        secrets.SystemRandom().randint()
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    @pytest.mark.parametrize(
        "input_code,expected_output",
        [
            (
                """
                import random
                import csv
                random.random()
                csv.excel
                """,
                """
                import csv
                import secrets

                secrets.SystemRandom().random()
                csv.excel
                """,
            ),
            (
                """
                import random
                from csv import excel
                random.random()
                excel
                """,
                """
                from csv import excel
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
        input_code = """
        random.random()

        import random"""
        expected_output = input_code
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_multifunctions(self, tmpdir):
        # Test that `random` import isn't removed if code uses part of the random
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """
        import random

        random.random()
        random.__all__
        """

        expected_output = """
        import random
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

    def test_sampling(self, tmpdir):
        input_code = """
        import random

        random.sample(["a", "b"], 1)
        random.choice(["a", "b"])
        random.choices(["a", "b"])
        """
        expected_output = """
        import secrets

        secrets.SystemRandom().sample(["a", "b"], 1)
        secrets.choice(["a", "b"])
        secrets.SystemRandom().choices(["a", "b"])
        """

        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=3)

    def test_from_import_choice(self, tmpdir):
        input_code = """
        from random import choice

        choice(["a", "b"])
        """
        expected_output = """
        import secrets

        secrets.choice(["a", "b"])
        """

        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=1)
