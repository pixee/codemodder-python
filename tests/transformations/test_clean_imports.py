from libcst.codemod import CodemodTest
from codemodder.codemods.transformations.clean_imports import CleanImports
from pathlib import Path


class TestCleanImports(CodemodTest):
    TRANSFORM = CleanImports

    def test_from_combine(self):
        before = """
        from a import Object
        from a import Object2

        print(Object)
        print(Object2)
        """

        after = """
        from a import Object, Object2

        print(Object)
        print(Object2)
        """

        self.assertCodemod(before, after, src_path=Path(""))

    def test_natural_order(self):
        before = """
        from a import Object11
        from a import Object1

        print(Object11)
        print(Object1)
        """

        after = """
        from a import Object1, Object11

        print(Object11)
        print(Object1)
        """

        self.assertCodemod(before, after, src_path=Path(""))

    def test_remove_unused(self):
        before = """
        from a import Object1
        """

        after = """"""

        self.assertCodemod(before, after, src_path=Path(""))

    def test_wont_remove_unused_future(self):
        before = """
        from __future__ import absolute_import
        """

        after = before

        self.assertCodemod(before, after, src_path=Path(""))

    def test_organize_by_sections(self):
        before = """
        from codemodder.codemods.transformations.clean_imports import CleanImports
        import os
        from third_party import Object
        from __future__ import absolute_import
        from .local import Object2

        print(Object)
        print(os)
        print(CleanImports)
        print(absolute_import)
        print(Object2)
        """

        after = """
        from __future__ import absolute_import

        import os

        from third_party import Object

        from codemodder.codemods.transformations.clean_imports import CleanImports

        from .local import Object2

        print(Object)
        print(os)
        print(CleanImports)
        print(absolute_import)
        print(Object2)
        """

        self.assertCodemod(before, after, src_path=Path("."))

    def test_will_ignore_local_imports(self):
        before = """
        import global2
        import global1

        def f():
            import b
            import a
            print(a)
            print(b)
        print(global1)
        print(global2)
        """

        after = """
        import global1
        import global2

        def f():
            import b
            import a
            print(a)
            print(b)
        print(global1)
        print(global2)
        """
        self.assertCodemod(before, after, src_path=Path(""))

    def test_it_can_change_behavior(self):
        # note that c will change from b to e due to the sort
        before = """
        from d import e as c
        from a import b as c

        c()
        """

        after = """
        from a import b as c
        from d import e as c

        c()
        """
        self.assertCodemod(before, after, src_path=Path(""))
