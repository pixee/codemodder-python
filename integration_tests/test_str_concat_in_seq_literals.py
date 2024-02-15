from core_codemods.str_concat_in_seq_literal import StrConcatInSeqLiteral
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestStrConcatInSeqLiteral(BaseIntegrationTest):
    codemod = StrConcatInSeqLiteral
    code_path = "tests/samples/str_concat_in_sequence_literals.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """    "ab",\n"""),
            (4, """    "gh",\n"""),
        ],
    )

    # fmt: off
    expected_diff =(
    """--- \n"""
    """+++ \n"""
    """@@ -1,7 +1,7 @@\n"""
    """ bad = [\n"""
    """-    "ab"\n"""
    """+    "ab",\n"""
    """     "cd",\n"""
    """     "ef",\n"""
    """-    "gh"\n"""
    """+    "gh",\n"""
    """     "ij",\n"""
    """ ]\n""")
    # fmt: on

    expected_line_change = "1"
    change_description = StrConcatInSeqLiteral.change_description
    num_changes = 2
