from textwrap import dedent

import libcst as cst
from libcst.codemod import Codemod, CodemodContext

from codemodder.codemods.utils_mixin import NameResolutionMixin


class TestNameResolutionMixin:
    def test_imported_prefix(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.get_aliased_prefix_name(node, "a.b")
                assert maybe_name == "alias"
                return tree

        input_code = dedent(
            """\
        import a.b as alias
        alias.c[0].d()
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_no_imported_prefix(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.get_aliased_prefix_name(node, "a.b")
                assert maybe_name is None
                return tree

        input_code = dedent(
            """\
        c[0].d()
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_base_name_from_import(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.find_base_name(node.func)
                assert maybe_name == "sys.executable.capitalize"
                return tree

        input_code = dedent(
            """\
        from sys import executable as exec
        exec.capitalize()
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_base_name_import(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.find_base_name(node.func)
                assert maybe_name == "sys.executable.capitalize"
                return tree

        input_code = dedent(
            """\
        import sys.executable as exec
        exec.capitalize()
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_base_name_no_assignment(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.find_base_name(node.func)
                assert maybe_name == "foo"
                return tree

        input_code = dedent(
            """\
        foo('hello world')
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_base_name_built_in(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.find_base_name(node.func)
                assert maybe_name == "builtins.print"
                return tree

        input_code = dedent(
            """\
        print('hello world')
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_find_names_within_scope(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                node = cst.ensure_type(tree.body[-2].body.body[1], cst.FunctionDef)

                names = self.find_used_names_within_nodes_scope(node)
                assert names == {
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "one",
                    "two",
                    "three",
                    "four",
                    "five",
                }
                return tree

        input_code = dedent(
            """\
        import a
        b = 1
        def one():
            c = 2
            def two():
                d = 3
            def three():
                e = 4
                def four():
                    f = 5
        def five():
            g = 6
            def six():
                h = 7
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_generate_available_name(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                node = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)

                name = self.generate_available_name(node, ["a", "b", "c"])
                assert name == "a_2"
                return tree

        input_code = dedent(
            """\
        import a
        import b
        import c
        a_1 = 1
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)
