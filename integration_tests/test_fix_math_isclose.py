from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_math_isclose import FixMathIsClose, FixMathIsCloseTransformer


class TestFixMathIsClose(BaseIntegrationTest):
    codemod = FixMathIsClose
    original_code = """
    import math

    def foo(a):
        return math.isclose(a, 0)
    """
    expected_new_code = """
    import math

    def foo(a):
        return math.isclose(a, 0, abs_tol=1e-09)
    """
    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,4 +1,4 @@\n"""
        """ import math\n"""
        """ \n"""
        """ def foo(a):\n"""
        """-    return math.isclose(a, 0)\n"""
        """+    return math.isclose(a, 0, abs_tol=1e-09)"""
    )
    # fmt: on
    expected_line_change = "4"
    change_description = FixMathIsCloseTransformer.change_description
