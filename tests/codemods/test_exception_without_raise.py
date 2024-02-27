from codemodder.codemods.test import BaseCodemodTest
from core_codemods.exception_without_raise import ExceptionWithoutRaise


class TestExceptionWithoutRaise(BaseCodemodTest):
    codemod = ExceptionWithoutRaise

    def test_name(self):
        assert self.codemod.name == "exception-without-raise"

    def test_simple(self, tmpdir):
        input_code = """
        ValueError
        """
        expected = """
        raise ValueError
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_call(self, tmpdir):
        input_code = """
        ValueError("Bad value!")
        """
        expected = """
        raise ValueError("Bad value!")
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_alias(self, tmpdir):
        input_code = """
        from decimal import Overflow as error
        error
        """
        expected = """
        from decimal import Overflow as error
        raise error
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_unknown_exception(self, tmpdir):
        input_code = """
        Something
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_raised_exception(self, tmpdir):
        input_code = """
        raise ValueError
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        print(1)
        ValueError("Bad value!")
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
