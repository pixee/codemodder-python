from core_codemods.use_set_literal import UseSetLiteral
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestUseSetLiteral(BaseIntegrationTest):
    codemod = UseSetLiteral
    code_path = "tests/samples/set_literal.py"

    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [(0, "x = {1, 2, 3}\n"), (1, "y = set()\n")],
    )

    expected_diff = """\
--- 
+++ 
@@ -1,2 +1,2 @@
-x = set([1, 2, 3])
-y = set([])
+x = {1, 2, 3}
+y = set()
"""

    expected_line_change = "1"
    num_changes = 2
    change_description = UseSetLiteral.CHANGE_DESCRIPTION
