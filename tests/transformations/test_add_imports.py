from libcst.codemod import CodemodTest
from libcst.codemod.visitors import AddImportsVisitor
from libcst.codemod.visitors import ImportItem


class TestAddImports(CodemodTest):
    TRANSFORM = AddImportsVisitor

    def test_add_only_at_top(self):
        before = """
        b()
        import a
        """

        after = """
        import b

        b()
        import a
        """

        self.assertCodemod(before, after, imports=[ImportItem("b", None, None)])

    def test_may_duplicate_imports(self):
        before = """
        a()
        import a
        """

        after = """
        import a

        a()
        import a
        """
        self.assertCodemod(before, after, imports=[ImportItem("a", None, None)])

    def test_may_duplicate_from_imports(self):
        before = """
        y()
        from a import x
        """

        after = """
        from a import y

        y()
        from a import x
        """
        self.assertCodemod(before, after, imports=[ImportItem("a", "y", None)])
