from codemodder.codemods.test import BaseCodemodTest
from core_codemods.remove_unnecessary_f_str import RemoveUnnecessaryFStr


class TestFStr(BaseCodemodTest):
    codemod = RemoveUnnecessaryFStr

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
        self.run_and_assert(tmpdir, before, after, num_changes=3)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        bad: str = f"bad" + "bad"
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
