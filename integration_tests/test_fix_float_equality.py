from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_float_equality import (
    FixFloatEquality,
    FixFloatEqualityTransformer,
)


class TestFixFloatEquality(BaseIntegrationTest):
    codemod = FixFloatEquality
    original_code = """
    def foo(a, b):
        return a == b - 0.1
    """
    expected_new_code = """
    import math
    
    def foo(a, b):
        return math.isclose(a, b - 0.1, rel_tol=1e-09, abs_tol=0.0)
    """
    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -1,2 +1,4 @@\n"""
        """+import math\n"""
        """+\n"""
        """ def foo(a, b):\n"""
        """-    return a == b - 0.1\n"""
        """+    return math.isclose(a, b - 0.1, rel_tol=1e-09, abs_tol=0.0)"""
    )
    # fmt: on
    expected_line_change = "2"
    change_description = FixFloatEqualityTransformer.change_description
