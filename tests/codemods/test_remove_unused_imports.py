from pathlib import Path

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.remove_unused_imports import RemoveUnusedImports


class TestRemoveUnusedImports(BaseCodemodTest):
    codemod = RemoveUnusedImports

    def test_no_change(self, tmpdir):
        before = r"""import a
from b import c
a
c
"""
        self.run_and_assert(tmpdir, before, before)

    def test_change(self, tmpdir):
        before = r"""import a
"""
        after = r"""
"""
        self.run_and_assert(tmpdir, before, after)

    def test_remove_import(self, tmpdir):
        before = r"""import a
import b
a
"""
        after = r"""import a
a
"""

        self.run_and_assert(tmpdir, before, after)

    def test_remove_single_from_import(self, tmpdir):
        before = r"""from b import c, d
c
"""

        after = r"""from b import c
c
"""
        self.run_and_assert(tmpdir, before, after)

    def test_remove_from_import(self, tmpdir):
        before = r"""from b import c
"""

        after = "\n"
        self.run_and_assert(tmpdir, before, after)

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

    def test_no_import_star_removal(self, tmpdir):
        before = r"""import a
from b import *
a.something
"""
        self.run_and_assert(tmpdir, before, before)

    def test_keep_format(self, tmpdir):
        before = "from a import b,c,d   \nprint(b)\nprint(d)"
        after = "from a import b,d   \nprint(b)\nprint(d)"
        self.run_and_assert(tmpdir, before, after)

    def test_dont_remove_if_noqa_before(self, tmpdir):
        before = "import a\n#   noqa\nimport b\na()"
        self.run_and_assert(tmpdir, before, before)

    def test_dont_remove_if_noqa_trailing(self, tmpdir):
        before = "import a\nimport b # noqa\na()"
        self.run_and_assert(tmpdir, before, before)

    def test_dont_remove_if_noqa_trailing_multiline(self, tmpdir):
        before = """
        from _pytest.assertion.util import (  # noqa: F401
            format_explanation as _format_explanation,
        )"""

        self.run_and_assert(tmpdir, before, before)

    def test_dont_remove_if_pylint_disable(self, tmpdir):
        before = "import a\nimport b # pylint: disable=W0611\na()"
        self.run_and_assert(tmpdir, before, before)

    def test_dont_remove_if_pylint_disable_next(self, tmpdir):
        before = (
            "import a\n#   pylint: disable-next=no-member, unused-import\nimport b\na()"
        )
        self.run_and_assert(tmpdir, before, before)

    def test_ignore_init_files(self, tmpdir):
        before = "import a"
        tmp_file_path = Path(tmpdir / "__init__.py")
        self.run_and_assert(tmpdir, before, before, files=[tmp_file_path])

    def test_no_pyling_pragma_in_comment_trailing(self, tmpdir):
        before = "import a # bogus: no-pragma"
        after = ""
        self.run_and_assert(tmpdir, before, after)

    def test_no_pyling_pragma_in_comment_before(self, tmpdir):
        before = "#header\nprint('hello')\n# bogus: no-pragma\nimport a "
        after = "#header\nprint('hello')"
        self.run_and_assert(tmpdir, before, after)
