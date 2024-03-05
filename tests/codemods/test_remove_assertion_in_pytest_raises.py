from codemodder.codemods.test import BaseCodemodTest
from core_codemods.remove_assertion_in_pytest_raises import (
    RemoveAssertionInPytestRaises,
)


class TestRemoveAssertionInPytestRaises(BaseCodemodTest):
    codemod = RemoveAssertionInPytestRaises

    def test_name(self):
        assert self.codemod.name == "remove-assertion-in-pytest-raises"

    def test_simple(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
                assert True
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_alias(self, tmpdir):
        input_code = """
        from pytest import raises as rise
        def foo():
            with rise(ZeroDivisionError):
                1/0
                assert True
        """
        expected = """
        from pytest import raises as rise
        def foo():
            with rise(ZeroDivisionError):
                1/0
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_from_import(self, tmpdir):
        input_code = """
        from pytest import raises
        def foo():
            with raises(ZeroDivisionError):
                1/0
                assert True
        """
        expected = """
        from pytest import raises
        def foo():
            with raises(ZeroDivisionError):
                1/0
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_all_asserts(self, tmpdir):
        # this is more of an edge case
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                assert True
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                pass
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_raises(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), pytest.raises(IndexError):
                1/0
                [1,2][3]
                assert True
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), pytest.raises(IndexError):
                1/0
                [1,2][3]
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_asserts(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
                assert 1
                assert 2
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert 1
            assert 2
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_asserts_mixed_early(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0; assert 1; assert 2
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert 1
            assert 2
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_asserts_mixed(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
                assert 1; assert 2
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError):
                1/0
            assert 1
            assert 2
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_simple_suite(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0; assert True
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0
            assert True
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_suite(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0; assert True; assert False;
        """
        expected = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError): 1/0
            assert True
            assert False
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_with_item_not_raises(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), open('') as file:
                1/0
                assert True
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_no_assertion_at_end(self, tmpdir):
        input_code = """
        import pytest
        def foo():
            with pytest.raises(ZeroDivisionError), open('') as file:
                assert True
                1/0
        """
        self.run_and_assert(tmpdir, input_code, input_code)
