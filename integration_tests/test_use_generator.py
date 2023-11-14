from core_codemods.use_generator import UseGenerator
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestUseGenerator(BaseIntegrationTest):
    codemod = UseGenerator
    code_path = "tests/samples/use_generator.py"

    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [(5, "x = sum(i for i in range(1000))\n")],
    )

    expected_diff = """\
--- 
+++ 
@@ -3,5 +3,5 @@
         yield i
 
 
-x = sum([i for i in range(1000)])
+x = sum(i for i in range(1000))
 y = some([i for i in range(1000)])
"""

    expected_line_change = "6"
    change_description = UseGenerator.CHANGE_DESCRIPTION
