from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_float_equality import FixFloatEquality


class TestNumpyNanEquality(BaseCodemodTest):
    codemod = FixFloatEquality

    def test_name(self):
        assert self.codemod.name == "fix-float-equality"

    def test_change(self, tmpdir):
        input_code = """
        0.2 == 2 - 0.1
        
        0.01 + 1 == 1
        
        a = 1.0
        b = 3.111
        a != b
        """
        expected = """
        import math
        
        math.isclose(0.2, 2 - 0.1, rel_tol=1e-09, abs_tol=0.0)
        
        math.isclose(0.01 + 1, 1, rel_tol=1e-09, abs_tol=0.0)
        
        a = 1.0
        b = 3.111
        not math.isclose(a, b, rel_tol=1e-09, abs_tol=0.0)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    def test_change_resolve_float(self, tmpdir):
        input_code = """
        def foo(a, b):
            return a == b + 0.1

        def foo(b):
            a = 1.02
            return a != b + 2

        """
        expected = """
        import math

        def foo(a, b):
            return math.isclose(a, b + 0.1, rel_tol=1e-09, abs_tol=0.0)

        def foo(b):
            a = 1.02
            return not math.isclose(a, b + 2, rel_tol=1e-09, abs_tol=0.0)

        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_change_if_asserts(self, tmpdir):
        input_code = """
        a = 1.0
        b = 3.111
        if a != b:
            pass
        
        assert a == b and 1 + a != b
        assert a != b 
        """
        expected = """
        import math

        a = 1.0
        b = 3.111
        if not math.isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
            pass
        
        assert math.isclose(a, b, rel_tol=1e-09, abs_tol=0.0) and not math.isclose(1 + a, b, rel_tol=1e-09, abs_tol=0.0)
        assert not math.isclose(a, b, rel_tol=1e-09, abs_tol=0.0) 
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=4)

    def test_change_math_already_imported(self, tmpdir):
        input_code = """
        import math

        math.e != 3 - 0.1
        """
        expected = """
        import math

        not math.isclose(math.e, 3 - 0.1, rel_tol=1e-09, abs_tol=0.0)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=1)

    def test_no_change(self, tmpdir):
        input_code = """
        2 == 1 + 1
        
        a = 3
        b = 3
        if a != b:
            pass
        
        a is b - 0.11
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_no_change_unknown_type(self, tmpdir):
        input_code = """
        def foo(a, b):
            return a == b
            
        def foo(a, b):
            return a - 10 == b
        
        def foo(b):
            a = 1
            return a == b + 1
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        0.2 == 2 - 0.1
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
