from collections import defaultdict
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.secure_random import SecureRandom
from codemodder.file_context import FileContext


class TestSecureRandom:
    RESULTS_BY_ID = defaultdict(
        list,
        {
            "secure-random": [
                {
                    "fingerprints": {"matchBasedId/v1": "3f3a "},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": "tests/samples/insecure_random.py",
                                    "uriBaseId": "%SRCROOT% ",
                                },
                                "region": {
                                    "endColumn": 16,
                                    "endLine": 3,
                                    "snippet": {"text": "random.random() "},
                                    "startColumn": 1,
                                    "startLine": 3,
                                },
                            }
                        }
                    ],
                    "message": {"text": "Insecure Random "},
                    "properties": {},
                    "ruleId": "codemodder.codemods.semgrep.secure-random ",
                }
            ]
        },
    )

    def run_and_assert(self, input_code, expexted_output):
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(
            Path("tests/samples/insecure_random.py"),
            False,
            [],
            [],
            self.RESULTS_BY_ID,
        )
        command_instance = SecureRandom(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expexted_output

    def test_with_empty_results(self):
        input_code = """import random

random.random()
var = "hello"
"""
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(Path(""), False, [], [], defaultdict(list))
        command_instance = SecureRandom(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == input_code

    def test_rule_ids(self):
        assert SecureRandom.RULE_IDS == ["secure-random"]

    def test_import_random(self):
        input_code = """import random

random.random()
var = "hello"
"""
        expexted_output = """import secrets

gen = secrets.SystemRandom()

gen.uniform(0, 1)
var = "hello"
"""

        self.run_and_assert(input_code, expexted_output)

    @pytest.mark.skip()
    def test_from_random(self):
        input_code = """from random import random

random()
var = "hello"
"""
        expexted_output = """import secrets

gen = secrets.SystemRandom()
gen.uniform(0, 1)
var = "hello"
"""
        self.run_and_assert(input_code, expexted_output)

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
    def test_random_randint(self, input_code, expexted_output):
        self.run_and_assert(input_code, expexted_output)

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
    def test_random_other_import_untouched(self, input_code, expexted_output):
        self.run_and_assert(input_code, expexted_output)

    def test_random_nameerror(self):
        input_code = """random.random()

import random"""
        expexted_output = input_code
        self.run_and_assert(input_code, expexted_output)

    def test_random_multifunctions(self):
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

        self.run_and_assert(input_code, expexted_output)
