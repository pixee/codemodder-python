from textwrap import dedent

from core_codemods.remove_future_imports import RemoveFutureImports
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestRemoveFutureImports(BaseIntegrationTest):
    codemod = RemoveFutureImports
    code_path = "tests/samples/future_imports.py"

    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = dedent(
        """\
    from __future__ import annotations

    print("HEY")
    """
    )

    expected_diff = """\
--- 
+++ 
@@ -1,4 +1,3 @@
-from __future__ import absolute_import
-from __future__ import *
+from __future__ import annotations
 
 print("HEY")
"""

    num_changes = 2
    expected_line_change = "1"
    change_description = RemoveFutureImports.CHANGE_DESCRIPTION
