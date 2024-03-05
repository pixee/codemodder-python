from libcst.codemod import CodemodTest

from codemodder.codemods.transformations.remove_unused_imports import (
    RemoveUnusedImportsCodemod,
)


class TestCleanImports(CodemodTest):
    TRANSFORM = RemoveUnusedImportsCodemod

    def test_remove_unused(self):
        before = """
        import a
        from b import c
        """

        after = ""

        self.assertCodemod(before, after)

    def test_keep_used(self):
        before = """
        import a
        from b import c
        print(c)
        """

        after = """
        from b import c
        print(c)
        """

        self.assertCodemod(before, after)

    def test_keep_future(self):
        before = """
        from __future__ import absolute_import
        """

        after = """
        from __future__ import absolute_import
        """

        self.assertCodemod(before, after)
