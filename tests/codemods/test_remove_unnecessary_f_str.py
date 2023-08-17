from codemodder.codemods.remove_unnecessary_f_str import UnnecessaryFStr
from tests.codemods.base_codemod_test import BaseCodemodTest


class TestLimitReadline(BaseCodemodTest):
    codemod = UnnecessaryFStr

    def test_no_change(self, tmpdir):
        before = r"""
good: str = "good"
good: str = f"with_arg{arg}"
good = "good{arg1}".format(1234)
good = "good".format()
good = "good" % {}
good = "good" % ()
good = rf"good\d+{bar}"
good = f"wow i don't have args but don't mess my braces {{ up }}"
"""
        self.run_and_assert(tmpdir, before, before)
        assert len(self.codemod.CHANGES_IN_FILE) == 0

    def test_change(self, tmpdir):
        before = r"""
bad: str = f"bad" + "bad"
bad: str = f'bad'
bad: str = rf'bad\d+'
"""
        after = r"""
bad: str = "bad" + "bad"
bad: str = 'bad'
bad: str = r'bad\d+'
"""
        self.run_and_assert(tmpdir, before, after)
        assert len(self.codemod.CHANGES_IN_FILE) == 3
