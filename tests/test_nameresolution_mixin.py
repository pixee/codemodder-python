import libcst as cst
from libcst.codemod import Codemod, CodemodContext
from codemodder.codemods.utils_mixin import NameResolutionMixin
from textwrap import dedent


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

    def test_get_base_name_no_import(self):
        class TestCodemod(Codemod, NameResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                maybe_name = self.find_base_name(node.func)
                assert maybe_name == "exec.capitalize"
                return tree

        input_code = dedent(
            """\
        exec.capitalize()
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)
