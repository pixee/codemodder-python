from codemodder.codemods.test import BaseCodemodTest
from core_codemods.invert_boolean_check import InvertedBooleanCheck


class TestInvertedBooleanCheck(BaseCodemodTest):
    codemod = InvertedBooleanCheck

    def test_no_change(self, tmpdir):
        before = """
        if not True:
            pass
        
        assert not hello()
        """
        self.run_and_assert(tmpdir, before, before)

    def test_change(self, tmpdir):
        before = """
        a = 5
        i = 20
        x = a
        y = x
        z = x
        n = 5
        m = 0
        status = True
        
        
        def finished():
            return True
        
        
        user_input = "hi"
        
        if not a == 2:
            b = not i < 10
        
        if not x != y:
            z = not m <= n
        
        if not status is True:
            pass
        
        if not finished() is False:
            pass
        
        assert not user_input == "yes"
        """
        after = """
        a = 5
        i = 20
        x = a
        y = x
        z = x
        n = 5
        m = 0
        status = True
        
        
        def finished():
            return True
        
        
        user_input = "hi"
        
        if a != 2:
            b = i >= 10
        
        if x == y:
            z = m > n
        
        if not status:
            pass
        
        if finished():
            pass
        
        assert user_input != "yes"
        """
        self.run_and_assert(tmpdir, before, after, num_changes=7)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        b = not i < 10
        """
        lines_to_exclude = [2]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
