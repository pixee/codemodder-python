import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_mutable_params import FixMutableParams


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
    def test_fix_single_arg_suite(self, tmpdir, mutable):
        input_code = f"""
        def foo(bar={mutable}): print(bar)
        """
        expected_output = f"""
        def foo(bar=None): bar = {mutable} if bar is None else bar; print(bar)
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

    def test_fix_overloaded(self, tmpdir):
        input_code = """
        from typing import overload
        @overload
        def foo(a : list[str] = []) -> str:
            ...
        @overload
        def foo(a : list[int] = []) -> int:
            ...
        def foo(a : list[int] | list[str] = []) -> int|str:
            return 0
        """
        expected_output = """
        from typing import Optional, overload
        @overload
        def foo(a : Optional[list[str]] = None) -> str:
            ...
        @overload
        def foo(a : Optional[list[int]] = None) -> int:
            ...
        def foo(a : Optional[list[int] | list[str]] = None) -> int|str:
            a = [] if a is None else a
            return 0
        """
        self.run_and_assert(tmpdir, input_code, expected_output, num_changes=3)

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

    @pytest.mark.parametrize(
        "mutable,annotation", [("[]", "List"), ("{}", "Dict"), ("set()", "Set")]
    )
    def test_fix_with_type_annotation(self, tmpdir, mutable, annotation):
        input_code = f"""
        from typing import {annotation}

        def foo(bar: {annotation}[int] = {mutable}):
            print(bar)
        """
        expected_output = f"""
        from typing import Optional, {annotation}

        def foo(bar: Optional[{annotation}[int]] = None):
            bar = {mutable} if bar is None else bar
            print(bar)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize(
        "mutable,annotation", [("[]", "list"), ("{}", "dict"), ("set()", "set")]
    )
    def test_fix_with_type_annotation_new_import(self, tmpdir, mutable, annotation):
        input_code = f"""
        def foo(bar: {annotation}[int] = {mutable}):
            print(bar)
        """
        expected_output = f"""
        from typing import Optional

        def foo(bar: Optional[{annotation}[int]] = None):
            bar = {mutable} if bar is None else bar
            print(bar)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_one_type_annotation(self, tmpdir):
        input_code = """
        from typing import List

        def foo(x = [], y: List[int] = [], z = {}):
            print(x, y, z)
        """
        expected_output = """
        from typing import Optional, List

        def foo(x = None, y: Optional[List[int]] = None, z = None):
            x = [] if x is None else x
            y = [] if y is None else y
            z = {} if z is None else z
            print(x, y, z)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_multiple_type_annotations(self, tmpdir):
        input_code = """
        from typing import Dict, List

        def foo(x = [], y: List[int] = [], z: Dict[str, int] = {}):
            print(x, y, z)
        """
        expected_output = """
        from typing import Optional, Dict, List

        def foo(x = None, y: Optional[List[int]] = None, z: Optional[Dict[str, int]] = None):
            x = [] if x is None else x
            y = [] if y is None else y
            z = {} if z is None else z
            print(x, y, z)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_type_already_optional(self, tmpdir):
        input_code = """
        from typing import Optional, List

        def foo(x: Optional[List[int]] = []):
            print(x)
        """
        expected_output = """
        from typing import Optional, List

        def foo(x: Optional[List[int]] = None):
            x = [] if x is None else x
            print(x)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_respect_docstring(self, tmpdir):
        input_code = '''
        def func(foo=[]):
            """Here is a docstring"""
            print(foo)
        '''
        expected_output = '''
        def func(foo=None):
            """Here is a docstring"""
            foo = [] if foo is None else foo
            print(foo)
        '''
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_fix_respect_leading_comment(self, tmpdir):
        input_code = """
        def func(foo=[]):
            # Here is a comment
            print(foo)
        """
        expected_output = """
        def func(foo=None):
            foo = [] if foo is None else foo
            # Here is a comment
            print(foo)
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_dont_modify_abstractmethod_body(self, tmpdir):
        input_code = """
        from abc import ABC, abstractmethod

        class Foo(ABC):
            @abstractmethod
            def foo(self, bar=[]):
                pass
        """
        expected_output = """
        from abc import ABC, abstractmethod

        class Foo(ABC):
            @abstractmethod
            def foo(self, bar=None):
                pass
        """
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        def foo(one, *args, bar=[]):
            print(bar)
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
