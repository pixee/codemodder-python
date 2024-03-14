import libcst as cst
from libcst.codemod import Codemod, CodemodContext, CodemodTest

from codemodder.codemods.transformations.remove_empty_string_concatenation import (
    RemoveEmptyStringConcatenation,
)


class RemoveEmptyStringConcatenationCodemod(Codemod):
    def transform_module_impl(self, tree: cst.Module) -> cst.Module:
        return tree.visit(RemoveEmptyStringConcatenation(CodemodContext()))


class TestRemoveEmptyStringConcatenation(CodemodTest):
    TRANSFORM = RemoveEmptyStringConcatenationCodemod

    def test_left(self):
        before = """
        "" + "world"
        """

        after = """
        "world"
        """

        self.assertCodemod(before, after)

    def test_right(self):
        before = """
        "hello" + ""
        """

        after = """
        "hello"
        """

        self.assertCodemod(before, after)

    def test_both(self):
        before = """
        "" + ""
        """

        after = """
        ""
        """

        self.assertCodemod(before, after)

    def test_multiple(self):
        before = """
        "" + "whatever" +  ""
        "hello" + "" + "world"
        """

        after = """
        "whatever"
        "hello" + "world"
        """

        self.assertCodemod(before, after)

    def test_concatenated_string_right(self):
        before = """
        "hello" ""
        """

        after = """
        "hello"
        """

        self.assertCodemod(before, after)

    def test_concatenated_string_left(self):
        before = """
        "world"
        """

        after = """
        "world"
        """

        self.assertCodemod(before, after)

    def test_concatenated_string_multiple(self):
        before = """
        "" "whatever" ""
        "hello" "" "world"
        """

        after = """
        "whatever"
        "hello" "world"
        """

        self.assertCodemod(before, after)

    def test_multiple_mixed(self):
        before = (
            """
        "" + '' """
            """ + r''''''
        """
        )

        after = '""'

        self.assertCodemod(before, after)
