from codemodder.codemods.remove_unused_imports import RemoveUnusedImports
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestRemoveUnusedImports(BaseCodemodTest):
    codemod = RemoveUnusedImports

    def test_no_change(self, tmpdir):
        before = r"""import a
from b import c
a
c
"""
        self.run_and_assert(tmpdir, before, before)
        assert len(self.codemod.CHANGES_IN_FILE) == 0

    def test_change(self, tmpdir):
        before = r"""import a
"""
        after = r"""
"""
        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_remove_import(self, tmpdir):
        before = r"""import a
import b
a
"""
        after = r"""import a
a
"""

        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_remove_single_from_import(self, tmpdir):
        before = r"""from b import c, d
c
"""

        after = r"""from b import c
c
"""
        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_remove_from_import(self, tmpdir):
        before = r"""from b import c
"""

        after = "\n"
        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_remove_inner_import(self, tmpdir):
        before = r"""import a
def something():
    import b
    a.something()
"""
        after = r"""import a
def something():
    a.something()
"""

        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_no_import_star_removal(self, tmpdir):
        before = r"""import a
from b import *
a.something
"""
        self.run_and_assert(tmpdir, before, before)
