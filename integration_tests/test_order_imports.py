from codemodder.codemods.order_imports import OrderImports
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestOrderImports(BaseIntegrationTest):
    codemod = OrderImports
    code_path = "tests/samples/unordered_imports.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, "# comment b4\n"),
            (2, "# comment b5\n"),
            (3, "# comment b3\n"),
            (4, "# comment b1\n"),
            (5, "# comment b2\n"),
            (6, "import b\n"),
            (7, "import d\n"),
            (8, "# comment a\n"),
            (9, "from a import a1, a2\n"),
            (10, "\n"),
            (11, "a1\n"),
            (12, "a2\n"),
            (13, "b\n"),
            (14, "c\n"),
            (15, "d"),
            (17, ""),
            (18, ""),
            (19, ""),
            (20, ""),
            (21, ""),
        ],
    )

    expected_diff = "--- \n+++ \n@@ -1,19 +1,13 @@\n #!/bin/env python\n-from a import a2\n-\n+# comment b4\n+# comment b5\n+# comment b3\n # comment b1\n # comment b2\n import b\n-\n+import d\n # comment a\n-from a import a1\n-\n-# comment b3\n-import b, d\n-\n-# comment b4\n-# comment b5\n-import b\n+from a import a1, a2\n \n a1\n a2\n"
    expected_line_change = "2"
    change_description = OrderImports.CHANGE_DESCRIPTION
