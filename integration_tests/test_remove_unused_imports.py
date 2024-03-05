from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from core_codemods.remove_unused_imports import RemoveUnusedImports


class TestRemoveUnusedImports(BaseIntegrationTest):
    codemod = RemoveUnusedImports
    code_path = "tests/samples/unused_imports.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """from builtins import complex\n"""),
        ],
    )

    expected_diff = "--- \n+++ \n@@ -1,5 +1,5 @@\n import abc\n-from builtins import complex, dict\n+from builtins import complex\n \n abc\n complex\n"
    expected_line_change = 2
    change_description = RemoveUnusedImports.change_description
