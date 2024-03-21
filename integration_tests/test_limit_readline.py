from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.limit_readline import LimitReadline


class TestLimitReadline(BaseIntegrationTest):
    codemod = LimitReadline
    original_code = """
    file = open("some_file.txt")
    file.readline()
    """
    replacement_lines = [(2, "file.readline(5_000_000)\n")]
    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,2 +1,2 @@\n"""
        """ file = open("some_file.txt")\n"""
        """-file.readline()\n"""
        """+file.readline(5_000_000)\n""")
    # fmt: on
    expected_line_change = "2"
    change_description = LimitReadline.change_description
    # expected because output code points to fake file
    allowed_exceptions = (FileNotFoundError,)
