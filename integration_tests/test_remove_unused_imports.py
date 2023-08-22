from codemodder.codemods.remove_unused_imports import RemoveUnusedImports
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestRemoveUnusedImports(BaseIntegrationTest):
    codemod = RemoveUnusedImports
    code_path = "tests/samples/unused_imports.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """from b import c\n"""),
        ],
    )

    expected_diff = "--- \n+++ \n@@ -1,5 +1,5 @@\n import a\n-from b import c, d\n+from b import c\n \n a\n c\n"
    expected_line_change = 2
    change_description = RemoveUnusedImports.CHANGE_DESCRIPTION
