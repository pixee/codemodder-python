from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.str_concat_in_seq_literal import StrConcatInSeqLiteral


class TestStrConcatInSeqLiteral(BaseIntegrationTest):
    codemod = StrConcatInSeqLiteral
    original_code = """
        bad = [
            "ab"
            "cd",
            "ef",
            "gh"
            "ij",
        ]
    """
    replacement_lines = [
        (2, """    "ab",\n"""),
        (5, """    "gh",\n"""),
    ]
    # fmt: off
    expected_diff = (
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
