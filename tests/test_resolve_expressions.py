from textwrap import dedent

import libcst as cst
from libcst.codemod import Codemod, CodemodContext

from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin


class TestResolveExpression:
    def test_resolve_expression_transitive(self):
        class TestCodemod(Codemod, NameAndAncestorResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                first_stmt = cst.ensure_type(tree.body[0], cst.SimpleStatementLine)
                assign = cst.ensure_type(first_stmt.body[0], cst.Assign)

                resolved = self.resolve_expression(node)
                assert resolved == assign.value
                return tree

        input_code = dedent(
            """\
        b = 'resolved'
        a = b
        name = a
        name
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_resolve_expression_imported_name(self):
        class TestCodemod(Codemod, NameAndAncestorResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                second_stmt = cst.ensure_type(tree.body[1], cst.SimpleStatementLine)
                assign = cst.ensure_type(second_stmt.body[0], cst.Assign)

                resolved = self.resolve_expression(node)
                assert resolved == assign.value
                return tree

        input_code = dedent(
            """\
        from x import y
        a = y
        name = a
        name
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_not_resolved_idempotent(self):
        class TestCodemod(Codemod, NameAndAncestorResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = expr.value

                resolved = self.resolve_expression(node)
                assert resolved == node
                return tree

        input_code = dedent(
            """\
        print('unresolved')
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_resolve_list_literal(self):
        class TestCodemod(Codemod, NameAndAncestorResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = cst.ensure_type(expr.value, cst.List)

                first = cst.ensure_type(
                    cst.ensure_type(tree.body[3], cst.SimpleStatementLine).body[0],
                    cst.Assign,
                ).value
                second = node.elements[1].value
                third = cst.ensure_type(
                    cst.ensure_type(tree.body[1], cst.SimpleStatementLine).body[0],
                    cst.Assign,
                ).value
                fourth = node.elements[-1]

                resolved = list(self.resolve_list_literal(node))
                assert resolved == [first, second, third, fourth]
                return tree

        input_code = dedent(
            """\
        from somewhere import unresolved
        third = 'third'
        rest = [third]
        first = 'first'
        [first, 'second', *rest, *unresolved]
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_resolve_dict_literal(self):
        class TestCodemod(Codemod, NameAndAncestorResolutionMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                stmt = cst.ensure_type(tree.body[-1], cst.SimpleStatementLine)
                expr = cst.ensure_type(stmt.body[0], cst.Expr)
                node = cst.ensure_type(expr.value, cst.Dict)

                first = cst.ensure_type(
                    cst.ensure_type(tree.body[3], cst.SimpleStatementLine).body[0],
                    cst.Assign,
                ).value
                second = node.elements[1].value
                third = cst.ensure_type(
                    cst.ensure_type(tree.body[1], cst.SimpleStatementLine).body[0],
                    cst.Assign,
                ).value

                first_key = node.elements[0].key
                second_key = node.elements[1].key
                third_key = (
                    cst.ensure_type(
                        cst.ensure_type(
                            cst.ensure_type(tree.body[2], cst.SimpleStatementLine).body[
                                0
                            ],
                            cst.Assign,
                        ).value,
                        cst.Dict,
                    )
                    .elements[0]
                    .key
                )

                resolved = self.resolve_dict(node)
                assert resolved == {
                    first_key: first,
                    second_key: second,
                    third_key: third,
                }
                return tree

        input_code = dedent(
            """\
        from somewhere import unresolved
        third = 'third'
        rest = {'3':third}
        first = 'first'
        {'1':first, '2':'second', **rest, **unresolved}
        """
        )
        tree = cst.parse_module(input_code)
        TestCodemod(CodemodContext()).transform_module(tree)
