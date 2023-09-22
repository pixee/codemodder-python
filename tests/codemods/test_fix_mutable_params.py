import pytest

from codemodder.codemods.fix_mutable_params import FixMutableParams
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestFixMutableParams(BaseCodemodTest):
    codemod = FixMutableParams

    # There's no literal for empty sets, so we use set() instead
    @pytest.mark.parametrize("mutable", ["[]", "{}", "set()"])
    def test_fix_single_arg(self, tmpdir, mutable):
        input_code = f"""
def foo(bar={mutable}):
    print(bar)
"""
        expected_output = f"""
def foo(bar=None):
    bar = {mutable} if bar is None else bar
    print(bar)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("mutable", ["[]", "{}", "set()"])
    def test_fix_single_arg_method(self, tmpdir, mutable):
        input_code = f"""
class Whatever:
    def foo(self, bar={mutable}):
        print(bar)
"""
        expected_output = f"""
class Whatever:
    def foo(self, bar=None):
        bar = {mutable} if bar is None else bar
        print(bar)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("mutable", ["[1, 2, 3]", '{"a": 42}', "{1, 2, 3}"])
    def test_with_values(self, tmpdir, mutable):
        input_code = f"""
def foo(bar={mutable}):
    print(bar)
"""
        expected_output = f"""
def foo(bar=None):
    bar = {mutable} if bar is None else bar
    print(bar)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("orig,updated", [("list()", "[]"), ("dict()", "{}")])
    def test_fix_single_arg_call_builtin(self, tmpdir, orig, updated):
        input_code = f"""
def foo(bar={orig}):
    print(bar)
"""
        expected_output = f"""
def foo(bar=None):
    bar = {updated} if bar is None else bar
    print(bar)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("mutable", ["list([1, 2, 3])", "dict({'a': 42})"])
    def test_fix_single_arg_call_builtin_with_values(self, tmpdir, mutable):
        input_code = f"""
def foo(bar={mutable}):
    print(bar)
"""
        expected_output = f"""
def foo(bar=None):
    bar = {mutable} if bar is None else bar
    print(bar)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_multiple_args(self, tmpdir):
        input_code = """
def foo(bar=[], baz={}):
    print(bar)
    print(baz)
"""
        expected_output = """
def foo(bar=None, baz=None):
    bar = [] if bar is None else bar
    baz = {} if baz is None else baz
    print(bar)
    print(baz)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_multiple_args_mixed(self, tmpdir):
        input_code = """
def foo(bar=[], x="hello", baz={"foo": 42}, biz=set(), boz=list(), buz={1, 2, 3}):
    print(bar)
    print(baz)
"""
        expected_output = """
def foo(bar=None, x="hello", baz=None, biz=None, boz=None, buz=None):
    bar = [] if bar is None else bar
    baz = {"foo": 42} if baz is None else baz
    biz = set() if biz is None else biz
    boz = [] if boz is None else boz
    buz = {1, 2, 3} if buz is None else buz
    print(bar)
    print(baz)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_only_one(self, tmpdir):
        input_code = """
def foo(bar="hello", baz={}):
    print(bar)
    print(baz)
"""
        expected_output = """
def foo(bar="hello", baz=None):
    baz = {} if baz is None else baz
    print(bar)
    print(baz)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)
