from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.fix_float_equality import FixFloatEqualityTransformer
from core_codemods.sonar.sonar_fix_float_equality import SonarFixFloatEquality


class TestSonarFixFloatEquality(SonarIntegrationTest):
    codemod = SonarFixFloatEquality
    code_path = "tests/samples/fix_float_equality.py"
    replacement_lines = [
        (1, "import math\n"),
        (2, "\n"),
        (3, "def foo(a, b):\n"),
        (4, "    return math.isclose(a, b - 0.1, rel_tol=1e-09, abs_tol=0.0)\n"),
    ]
    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,2 +1,4 @@\n"""
        """+import math\n"""
        """+\n"""
        """ def foo(a, b):\n"""
        """-    return a == b - 0.1\n"""
        """+    return math.isclose(a, b - 0.1, rel_tol=1e-09, abs_tol=0.0)\n"""
    )
    # fmt: on
    expected_line_change = "2"
    change_description = FixFloatEqualityTransformer.change_description
    num_changes = 1
