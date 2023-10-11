from core_codemods.order_imports import OrderImports
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
            (1, "# comment builtins4\n"),
            (2, "# comment builtins5\n"),
            (3, "# comment builtins3\n"),
            (4, "# comment builtins1\n"),
            (5, "# comment builtins2\n"),
            (6, "import builtins\n"),
            (7, "import collections\n"),
            (8, "import datetime\n"),
            (9, "# comment a\n"),
            (10, "from abc import ABC, ABCMeta\n"),
            (11, "\n"),
            (12, "ABC\n"),
            (13, "ABCMeta\n"),
            (14, "builtins\n"),
            (15, "collections\n"),
            (16, ""),
            (17, ""),
            (18, ""),
            (19, ""),
            (20, ""),
            (21, ""),
        ],
    )

    expected_diff = "--- \n+++ \n@@ -1,20 +1,14 @@\n #!/bin/env python\n-from abc import ABCMeta\n-\n+# comment builtins4\n+# comment builtins5\n+# comment builtins3\n # comment builtins1\n # comment builtins2\n import builtins\n-\n+import collections\n+import datetime\n # comment a\n-from abc import ABC\n-\n-# comment builtins3\n-import builtins, datetime\n-\n-# comment builtins4\n-# comment builtins5\n-import builtins\n-import collections\n+from abc import ABC, ABCMeta\n \n ABC\n ABCMeta\n"
    expected_line_change = "2"
    change_description = OrderImports.CHANGE_DESCRIPTION
