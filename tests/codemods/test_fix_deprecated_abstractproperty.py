import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_deprecated_abstractproperty import FixDeprecatedAbstractproperty

property_or_class = pytest.mark.parametrize(
    "deprecated_func, arg_name, new_func",
    [
        ("abstractproperty", "self", "property"),
        ("abstractclassmethod", "cls", "classmethod"),
        ("abstractstaticmethod", "arg", "staticmethod"),
    ],
)


@property_or_class
class TestFixDeprecatedAbstractproperty(BaseCodemodTest):
    codemod = FixDeprecatedAbstractproperty

    def test_import(self, tmpdir, deprecated_func, arg_name, new_func):
        original_code = f"""
        import abc

        class A:
            @abc.{deprecated_func}
            def foo({arg_name}):
                pass
        """
        new_code = f"""
        import abc

        class A:
            @{new_func}
            @abc.abstractmethod
            def foo({arg_name}):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_import_from(self, tmpdir, deprecated_func, arg_name, new_func):
        original_code = f"""
        from abc import {deprecated_func}

        class A:
            @{deprecated_func}
            def foo({arg_name}):
                pass
        """
        new_code = f"""
        import abc

        class A:
            @{new_func}
            @abc.abstractmethod
            def foo({arg_name}):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_import_alias(self, tmpdir, deprecated_func, arg_name, new_func):
        original_code = f"""
        from abc import {deprecated_func} as ap

        class A:
            @ap
            def foo({arg_name}):
                pass
        """
        new_code = f"""
        import abc

        class A:
            @{new_func}
            @abc.abstractmethod
            def foo({arg_name}):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_different_abstract(self, tmpdir, deprecated_func, arg_name, new_func):
        new_code = (
            original_code
        ) = f"""
        from xyz import {deprecated_func}

        class A:
            @{deprecated_func}
            def foo({arg_name}):
                pass

            @{new_func}
            def bar({arg_name}):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_preserve_decorator_order(
        self, tmpdir, deprecated_func, arg_name, new_func
    ):
        original_code = f"""
        import abc

        class A:
            @whatever
            @abc.{deprecated_func}
            def foo({arg_name}):
                pass
        """
        new_code = f"""
        import abc

        class A:
            @whatever
            @{new_func}
            @abc.abstractmethod
            def foo({arg_name}):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_preserve_comments(self, tmpdir, deprecated_func, arg_name, new_func):
        original_code = f"""
        import abc

        class A:
            @abc.{deprecated_func} # comment
            def foo({arg_name}):
                pass
        """
        new_code = f"""
        import abc

        class A:
            @{new_func} # comment
            @abc.abstractmethod
            def foo({arg_name}):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_exclude_line(self, tmpdir, deprecated_func, arg_name, new_func):
        input_code = (
            expected
        ) = f"""
        import abc

        class A:
            @abc.{deprecated_func}
            def foo({arg_name}):
                pass
        """
        lines_to_exclude = [5]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
