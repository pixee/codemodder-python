from tests.codemods.base_codemod_test import BaseCodemodTest
from codemodder.codemods.order_imports import OrderImports


class TestOrderImports(BaseCodemodTest):
    codemod = OrderImports

    def test_no_change(self, tmpdir):
        before = r"""import a
from b import c
"""
        self.run_and_assert(tmpdir, before, before)
        assert len(self.codemod.CHANGES_IN_FILE) == 0

    def test_separate_from_imports_and_regular(self, tmpdir):
        before = r"""import y
from a import c
import x"""

        after = r"""import x
import y
from a import c"""
        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_consolidate_from_imports(self, tmpdir):
        before = r"""from a import a1
from a import a3
from a import a2"""

        after = r"""from a import a1, a2, a3"""
        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1

    def test_order_blocks_separately(self, tmpdir):
        before = r"""import x
import a
print("")
import y
import b"""

        after = r"""import a
import x
print("")
import b
import y"""

        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 2

    def test_preserve_comments(self, tmpdir):
        before = r"""# do not move
import x
# comment a, d
import a, d
# from comment b1
from b import b1
# from comment b2
from b import b2
"""
        after = r"""# do not move
# comment a, d
import a
import d
import x
# from comment b2
# from comment b1
from b import b1, b2
"""

        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 1
