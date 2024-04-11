from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_math_isclose import FixMathIsClose


class TestFixMathIsClose(BaseCodemodTest):
    codemod = FixMathIsClose

    def test_name(self):
        assert self.codemod.name == "fix-math-isclose"

    def test_change(self, tmpdir):
        input_code = """
        import math
        
        math.isclose(a, 0, abs_tol=0.0)
        math.isclose(a, 0, abs_tol=0)
        math.isclose(0, 20)

        def foo(a):
            return math.isclose(a, 0)
        
        """
        expected = """
        import math
        
        math.isclose(a, 0, abs_tol=1e-09)
        math.isclose(a, 0, abs_tol=1e-09)
        math.isclose(0, 20, abs_tol=1e-09)

        def foo(a):
            return math.isclose(a, 0, abs_tol=1e-09)
        
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=4)

    def test_change_resolves_to_zero(self, tmpdir):
        input_code = """
        import math

        a = 0
        math.isclose(a, b)

        c = float(0.0)
        math.isclose(c, d)
        math.isclose(1, int(0.0))
        """
        expected = """
        import math

        a = 0
        math.isclose(a, b, abs_tol=1e-09)

        c = float(0.0)
        math.isclose(c, d, abs_tol=1e-09)
        math.isclose(1, int(0.0), abs_tol=1e-09)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    def test_no_change(self, tmpdir):
        input_code = """
        import math
        
        math.isclose(a, b) 
        math.isclose(5, 29) 
        math.isclose(a, 0, abs_tol=0.1)
        
        def bar(a, b):
            return math.isclose(a, b)
            
        math.isclose()
        math.isclose(2)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        import math
        math.isclose(20, 0)
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
