from codemodder.codemods.test import BaseCodemodTest
from core_codemods.order_imports import OrderImports


class TestOrderImports(BaseCodemodTest):
    codemod = OrderImports

    def test_no_change(self, tmpdir):
        before = r"""import a
from b import c
"""
        self.run_and_assert(tmpdir, before, before)

    def test_separate_from_imports_and_regular(self, tmpdir):
        before = r"""import y
from a import c
import x"""

        after = r"""import x
import y
from a import c"""
        self.run_and_assert(tmpdir, before, after)

    def test_consolidate_from_imports(self, tmpdir):
        before = r"""from a import a1
from a import a3
from a import a2"""

        after = r"""from a import a1, a2, a3"""
        self.run_and_assert(tmpdir, before, after)

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

        self.run_and_assert(tmpdir, before, after, num_changes=2)

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

    def test_handle_star_imports(self, tmpdir):
        before = r"""from a import x
from a import b
# comment *
from a import *"""

        after = r"""# comment *
from a import *
from a import b, x"""

        self.run_and_assert(tmpdir, before, after)

    def test_handle_composite_and_relative_imports(self, tmpdir):
        before = r"""from . import a
import a.b.c.d"""

        after = r"""import a.b.c.d

from . import a"""

        self.run_and_assert(tmpdir, before, after)

    def test_natural_order(self, tmpdir):
        before = """from a import Object11
from a import Object1
"""

        after = """from a import Object1, Object11
"""

        self.run_and_assert(tmpdir, before, after)

    def test_wont_remove_unused_future(self, tmpdir):
        before = """from __future__ import absolute_import
"""

        after = before

        self.run_and_assert(tmpdir, before, after)

    def test_organize_by_sections(self, tmpdir):
        before = """from codemodder.codemods.transformations.clean_imports import CleanImports
import os
from third_party import Object
from __future__ import absolute_import
from .local import Object2
"""

        after = """from __future__ import absolute_import

import os

from codemodder.codemods.transformations.clean_imports import CleanImports
from third_party import Object

from .local import Object2
"""

        self.run_and_assert(tmpdir, before, after)

    def test_will_ignore_non_top_level(self, tmpdir):
        before = """import global2
import global1

def f():
    import b
    import a

if True:
    import global3
"""

        after = """import global1
import global2

def f():
    import b
    import a

if True:
    import global3
"""
        self.run_and_assert(tmpdir, before, after)

    def test_it_can_change_behavior(self, tmpdir):
        # note that c will change from b to e due to the sort
        before = """from d import e as c
from a import b as c

c()
"""

        after = """from a import b as c
from d import e as c

c()
"""
        self.run_and_assert(tmpdir, before, after)
