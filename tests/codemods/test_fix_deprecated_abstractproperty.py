from core_codemods.fix_deprecated_abstractproperty import FixDeprecatedAbstractproperty
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestFixDeprecatedAbstractproperty(BaseCodemodTest):
    codemod = FixDeprecatedAbstractproperty

    def test_import(self, tmpdir):
        original_code = """
        import abc

        class A:
            @abc.abstractproperty
            def foo(self):
                pass
        """
        new_code = """
        import abc

        class A:
            @property
            @abc.abstractmethod
            def foo(self):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_import_from(self, tmpdir):
        original_code = """
        from abc import abstractproperty

        class A:
            @abstractproperty
            def foo(self):
                pass
        """
        new_code = """
        import abc

        class A:
            @property
            @abc.abstractmethod
            def foo(self):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_import_alias(self, tmpdir):
        original_code = """
        from abc import abstractproperty as ap

        class A:
            @ap
            def foo(self):
                pass
        """
        new_code = """
        import abc

        class A:
            @property
            @abc.abstractmethod
            def foo(self):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_different_abstractproperty(self, tmpdir):
        new_code = original_code = """
        from xyz import abstractproperty

        class A:
            @abstractproperty
            def foo(self):
                pass

            @property
            def bar(self):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_preserve_decorator_order(self, tmpdir):
        original_code = """
        import abc

        class A:
            @whatever
            @abc.abstractproperty
            def foo(self):
                pass
        """
        new_code = """
        import abc

        class A:
            @whatever
            @property
            @abc.abstractmethod
            def foo(self):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_preserve_comments(self, tmpdir):
        original_code = """
        import abc

        class A:
            @abc.abstractproperty # comment
            def foo(self):
                pass
        """
        new_code = """
        import abc

        class A:
            @property # comment
            @abc.abstractmethod
            def foo(self):
                pass
        """
        self.run_and_assert(tmpdir, original_code, new_code)

    def test_exclude_line(self, tmpdir):
        input_code = expected = """\
        import abc

        class A:
            @abc.abstractproperty
            def foo(self):
                pass
        """
        lines_to_exclude = [4]
        self.assert_no_change_line_excluded(
            tmpdir, input_code, expected, lines_to_exclude
        )
