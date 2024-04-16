import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.use_walrus_if import UseWalrusIf


class TestUseWalrusIf(BaseCodemodTest):
    codemod = UseWalrusIf

    @pytest.mark.parametrize(
        "condition",
        [
            "is None",
            "is not None",
            "== 42",
            '!= "bar"',
        ],
    )
    def test_simple_use_walrus_if(self, tmpdir, condition):
        input_code = f"""
        val = do_something()
        if val {condition}:
            do_something_else(val)
        """
        expected_output = f"""
        if (val := do_something()) {condition}:
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_walrus_if_name_only(self, tmpdir):
        input_code = """
        val = do_something()
        if val:
            do_something_else(val)
        """
        expected_output = """
        if val := do_something():
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_walrus_if_not(self, tmpdir):
        input_code = """
        val = do_something()
        if not val:
            do_something_else(val)
        """
        expected_output = """
        if not (val := do_something()):
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_walrus_if_preserve_comments(self, tmpdir):
        input_code = """
        val = do_something() # comment
        if val is not None: # another comment
            do_something_else(val)
        """
        expected_output = """
        # comment
        if (val := do_something()) is not None: # another comment
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_walrus_if_multiple(self, tmpdir):
        input_code = """
        val = do_something()
        if val is not None:
            do_something_else(val)

        foo = hello()
        if foo == "bar":
            whatever(foo)
        """
        expected_output = """
        if (val := do_something()) is not None:
            do_something_else(val)

        if (foo := hello()) == "bar":
            whatever(foo)
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_walrus_if_in_function(self, tmpdir):
        """Make sure this works inside more complex code"""
        input_code = """
        def foo():
            val = do_something()
            if val is not None:
                do_something_else(val)
        """
        expected_output = """
        def foo():
            if (val := do_something()) is not None:
                do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_walrus_if_nested(self, tmpdir):
        """Make sure this works inside more complex code"""
        input_code = """
        x = do_something()
        if x is not None:
            y = do_something_else(x)
            if y is not None:
                bizbaz(x, y)
        """
        expected_output = """
        if (x := do_something()) is not None:
            if (y := do_something_else(x)) is not None:
                bizbaz(x, y)
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=2)

    def test_walrus_if_used_inner(self, tmpdir):
        """Make sure this works inside more complex code"""
        input_code = """
        result = foo()
        if result is not None:
            if something_else():
                print(result)
        """
        expected_output = """
        if (result := foo()) is not None:
            if something_else():
                print(result)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("space", ["", "\n"])
    def test_with_whitespace(self, tmpdir, space):
        input_code = f"""
val = do_something(){space}
if val is not None:
    do_something_else(val)
        """
        expected_output = f"""
{space}if (val := do_something()) is not None:
    do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("variable", ["foo", "value", "oval"])
    def test_dont_apply_walrus_different_variable(self, tmpdir, variable):
        input_code = f"""
        val = do_something()
        if {variable} is not None:
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_dont_apply_walrus_method_call(self, tmpdir):
        input_code = """
        val = do_something()
        if val.method() is not None:
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_dont_apply_walrus_call_with_func(self, tmpdir):
        input_code = """
        val = do_something()
        if woot(val) is not None:
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_dont_apply_walrus_expr(self, tmpdir):
        input_code = """
        val = do_something()
        if val + 42 is not None:
            do_something_else(val)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize("comparator", [">", "<", ">=", "<="])
    def test_walrus_with_comparison(self, tmpdir, comparator):
        input_code = f"""
        def func(y):
            y = bar(y)
            x = foo()
            if x {comparator} y:
                print("whatever", y)
            """
        expected_output = f"""
        def func(y):
            y = bar(y)
            x = foo()
            if x {comparator} y:
                print("whatever", y)
            """
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.xfail(reason="Need to recompute line numbers to reflect removed lines")
    def test_multiple_walrus_changes(self, tmpdir):
        input_code = """
        val = do_something()
        if val is not None:
            do_something_else(val)

        foo = hello()
        if foo == "bar":
            whatever(foo)

        bar = do_something_else()
        if bar is not None:
            do_something(bar)
        """
        expected_output = """
        if (val := do_something()) is not None:
            do_something_else(val)

        if (foo := hello()) == "bar":
            whatever(foo)

        if (bar := do_something_else()) is not None:
            do_something(bar)
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=3)

        changes = self.changeset[0].changes
        assert changes[0].lineNumber == 2
        assert changes[1].lineNumber == 5
        assert changes[2].lineNumber == 8

    def test_no_walrus_if_unused_variable(self, tmpdir):
        input_code = """
        test = (
            1
            if True
            else 0
        )
        if test:
            print("var will not be reused")
        """
        expected_output = """
        if (
            1
            if True
            else 0
        ):
            print("var will not be reused")
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_no_walrus_if_not(self, tmpdir):
        input_code = """
        val = do_something()
        if not val:
            print("something")
        """
        expected_output = """
        if not do_something():
            print("something")
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_no_walrus_if(self, tmpdir):
        input_code = """
        val = do_something()
        if val is None:
            print("hi")
        """
        expected_output = """
        if do_something() is None:
            print("hi")
        """
        self.run_and_assert(tmpdir, input_code, expected_output)
