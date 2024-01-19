from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestRemoveAssertionInPytestRaises(BaseCodemodTest):
    codemod = RemoveAssertionInPytestRaises

    def test_name(self):
        assert self.codemod.name == "remove-assertion-in-pytest-raises"

    def test_simple(self, tmpdir):
        input_code = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
                assert True
        """
        expected = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_raises(self, tmpdir):
        input_code = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), pytest.raises(IndexError):
                1/0
                [1,2][3]
                assert True
        """
        expected = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), pytest.raises(IndexError):
                1/0
                [1,2][3]
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_asserts(self, tmpdir):
        input_code = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
                assert 1
                assert 2
        """
        expected = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert 1
            assert 2
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_simple_suite(self, tmpdir):
        input_code = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0; assert True
        """
        expected = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_suite(self, tmpdir):
        input_code = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0; assert True; assert False;
        """
        expected = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0
            assert True
            assert False
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_with_item_not_raises(self, tmpdir):
        input_code = """\
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), open('') as file:
                1/0
                assert True
        """
        self.run_and_assert(tmpdir, input_code, input_code)
