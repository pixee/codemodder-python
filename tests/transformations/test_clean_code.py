from libcst.codemod import CodemodTest

from codemodder.utils.clean_code import RemoveEmptyExpressionsFormatting


class TestRemoveEmptyExpressionsFormatting(CodemodTest):
    TRANSFORM = RemoveEmptyExpressionsFormatting

    def test_empty_string(self):
        before = """
        "string" % ""
        """

        after = """
        "string"
        """

        self.assertCodemod(before, after)

    def test_empty_dict(self):
        before = """
        "string" % {}
        """

        after = """
        "string"
        """

        self.assertCodemod(before, after)

    def test_empty_tuple(self):
        before = """
        "string" % ()
        """

        after = """
        "string"
        """

        self.assertCodemod(before, after)

    def test_single_dict_removal(self):
        before = """
        other_d = {'c':""}
        d = {'a':1, 'b':2, **other_d}
        "%(a)s%(b)s%(c)s" % d
        """

        after = """
        other_d = {}
        d = {'a':1, 'b':2, **other_d}
        "%(a)s%(b)s" % d
        """

        self.assertCodemod(before, after)

    def test_single_tuple_removal(self):
        before = """
        t = (1, "", 3,)
        "%s%s%s" % t
        """

        after = """
        t = (1, 3,)
        "%s%s" % t
        """

        self.assertCodemod(before, after)

    def test_remove_all_tuple(self):
        before = """
        t = ("", "", "",)
        "%s%s%s" % t
        """

        after = """
        t = ()
        ''
        """

        self.assertCodemod(before, after)

    def test_remove_all_dict(self):
        before = """
        d = {'a':"", 'b':""}
        "%(a)s%(b)s" % d
        """

        after = """
        d = {}
        ''
        """

        self.assertCodemod(before, after)
