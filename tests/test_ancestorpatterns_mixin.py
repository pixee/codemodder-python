from textwrap import dedent

import libcst as cst
from libcst.codemod import Codemod, CodemodContext

from codemodder.codemods.utils_mixin import AncestorPatternsMixin


class TestNameResolutionMixin:
    def test_get_parent(self):
        class TestCodemod(Codemod, AncestorPatternsMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)

                maybe_parent = self.get_parent(stmt)
                assert maybe_parent == tree
                return tree

        input_code = dedent(
            """\
        a = 1
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_parent_root(self):
        class TestCodemod(Codemod, AncestorPatternsMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                maybe_parent = self.get_parent(tree)
                assert maybe_parent is None
                return tree

        input_code = dedent(
            """\
        a = 1
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_path_to_root(self):
        class TestCodemod(Codemod, AncestorPatternsMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                node = stmt.body[0]

                path = self.path_to_root(node)
                assert len(path) == 2
                return tree

        input_code = dedent(
            """\
        a = 1
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_get_path_to_root_set(self):
        class TestCodemod(Codemod, AncestorPatternsMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                node = stmt.body[0]

                path = self.path_to_root_as_set(node)
                assert len(path) == 3
                return tree

        input_code = dedent(
            """\
        a = 1
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_is_ancestor(self):
        class TestCodemod(Codemod, AncestorPatternsMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                node = stmt.body[0]

                assert self.is_ancestor(node, tree)
                return tree

        input_code = dedent(
            """\
        a = 1
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)
