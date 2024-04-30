from codemodder.codemods.test import BaseCodemodTest
from core_codemods.break_or_continue_out_of_loop import BreakOrContinueOutOfLoop


class TestBreakOrContinueOutOfLoop(BaseCodemodTest):
    codemod = BreakOrContinueOutOfLoop

    def test_name(self):
        assert self.codemod.name == "break-or-continue-out-of-loop"

    def test_continue(self, tmpdir):
        input_code = """
        continue
        """
        expected = """
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_break(self, tmpdir):
        input_code = """
        break
        """
        expected = """
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_single_statement_in_block(self, tmpdir):
        input_code = """
        def f():
            break
        """
        expected = """
        def f():
            pass
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_results_in_empty_else(self, tmpdir):
        input_code = """
        def print_even_numbers():
            if i % 2 == 0:
                print(i)
            else:
                continue
                continue
                continue
        """
        expected = """
        def print_even_numbers():
            if i % 2 == 0:
                print(i)
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=3)

    def test_single_statement_in_suite(self, tmpdir):
        input_code = """
        def f(): break
        """
        expected = """
        def f(): pass
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_break_in_loop(self, tmpdir):
        input_code = """
        while True:
            break
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_continue_in_loop(self, tmpdir):
        input_code = """
        for i in range(0,1): continue
        """
        self.run_and_assert(tmpdir, input_code, input_code)
