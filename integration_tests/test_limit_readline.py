from core_codemods.limit_readline import LimitReadline
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestLimitReadline(BaseIntegrationTest):
    codemod = LimitReadline
    code_path = "tests/samples/unlimited_readline.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path, [(1, "file.readline(5_000_000)\n")]
    )
    expected_diff = '--- \n+++ \n@@ -1,2 +1,2 @@\n file = open("some_file.txt")\n-file.readline()\n+file.readline(5_000_000)\n'
    expected_line_change = "2"
    change_description = LimitReadline.CHANGE_DESCRIPTION
    # expected because output code points to fake file
    allowed_exceptions = (FileNotFoundError,)
