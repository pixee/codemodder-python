from codemodder.codemods.limit_readline import LimitReadline
from integration_tests.base_test import BaseIntegrationTest


class TestLimitReadline(BaseIntegrationTest):
    codemod = LimitReadline
    code_path = "tests/samples/unlimited_readline.py"
    original_code = 'file = open("some_file.txt")\nfile.readline()\n'
    expected_new_code = 'file = open("some_file.txt")\nfile.readline(5_000_000)\n'
    expected_diff = '--- \n+++ \n@@ -1,2 +1,2 @@\n file = open("some_file.txt")\n-file.readline()\n+file.readline(5_000_000)\n'
    expected_line_change = "2"
    change_description = LimitReadline.CHANGE_DESCRIPTION
