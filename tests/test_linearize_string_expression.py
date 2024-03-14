from textwrap import dedent

import libcst as cst
from libcst.codemod import Codemod, CodemodContext

from codemodder.utils.format_string_parser import extract_raw_value
from codemodder.utils.linearize_string_expression import LinearizeStringMixin


class TestLinearizeStringExpression:

    def test_linearize_concat(self):
        class TestCodemod(Codemod, LinearizeStringMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                node = tree.body[-1].body[0].value
                lse = self.linearize_string_expression(node)
                assert lse
                assert len(lse.parts) == 6
                return tree

        code = dedent(
            """\
        middle = 'third' + (1+2) + fifth
        "first" "second" + middle +  "sixth"
        """
        )
        tree = cst.parse_module(code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_linearize_format_string(self):
        class TestCodemod(Codemod, LinearizeStringMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                node = tree.body[-1].body[0].value
                lse = self.linearize_string_expression(node)
                assert lse
                assert len(lse.parts) == 6
                return tree

        code = dedent(
            """\
        from something import second, fourth
        f'first {second} third {f"{fourth} fifth"} sixth'
        """
        )
        tree = cst.parse_module(code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_linearize_printf_format(self):
        class TestCodemod(Codemod, LinearizeStringMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                node = tree.body[-1].body[0].value
                lse = self.linearize_string_expression(node)
                assert lse
                assert len(lse.parts) == 7
                assert len(lse.node_pieces.keys()) == 2
                assert {len(p) for p in lse.node_pieces.values()} == {4}
                return tree

        code = dedent(
            """\
        from something import fifth
        dict_rest = {'two': seventh}
        middle = "fourth %(one)s sixth %(two)s" % {'one':fifth, **dict_rest}
        "first %s third %s" % ("second", middle, )
        """
        )
        tree = cst.parse_module(code)
        TestCodemod(CodemodContext()).transform_module(tree)

    def test_linearize_mixed(self):
        class TestCodemod(Codemod, LinearizeStringMixin):
            def transform_module_impl(self, tree: cst.Module) -> cst.Module:
                node = tree.body[-1].body[0].value
                lse = self.linearize_string_expression(node)
                assert lse
                assert len(lse.parts) == 6
                assert [extract_raw_value(p) for p in lse.parts] == [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                ]
                return tree

        code = dedent(
            """\
        concat = "3" + "4"
        formatop = "2%s5" % concat
        f"1{formatop}6"
        """
        )
        tree = cst.parse_module(code)
        TestCodemod(CodemodContext()).transform_module(tree)
