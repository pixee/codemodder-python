from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.sonar.sonar_fix_math_isclose import (
    FixMathIsCloseSonarTransformer,
    SonarFixMathIsClose,
)


class TestSonarFixMathIsClose(SonarIntegrationTest):
    codemod = SonarFixMathIsClose
    code_path = "tests/samples/fix_math_isclose.py"
    replacement_lines = [(5, "    return math.isclose(a, 0, abs_tol=1e-09)\n")]
    expected_diff = "--- \n+++ \n@@ -2,4 +2,4 @@\n \n \n def foo(a):\n-    return math.isclose(a, 0)\n+    return math.isclose(a, 0, abs_tol=1e-09)\n"
    expected_line_change = "5"
    change_description = FixMathIsCloseSonarTransformer.change_description
