from codemodder.codemods.test import BaseCodemodTest
from core_codemods.use_set_literal import UseSetLiteral


class TestUseSetLiteral(BaseCodemodTest):
    codemod = UseSetLiteral

    def test_simple(self, tmpdir):
        original_code = """
        x = set([1, 2, 3])
        """
        expected_code = """
        x = {1, 2, 3}
        """
        self.run_and_assert(tmpdir, original_code, expected_code)

    def test_empty_list(self, tmpdir):
        original_code = """
        x = set([])
        """
        expected_code = """
        x = set()
        """
        self.run_and_assert(tmpdir, original_code, expected_code)

    def test_already_empty(self, tmpdir):
        original_code = """
        x = set()
        """
        self.run_and_assert(tmpdir, original_code, original_code)

    def test_not_builtin(self, tmpdir):
        original_code = """
        from whatever import set
        x = set([1, 2, 3])
        """
        self.run_and_assert(tmpdir, original_code, original_code)

    def test_not_list_literal(self, tmpdir):
        original_code = """
        x = set(some_previously_defined_list)
        """
        self.run_and_assert(tmpdir, original_code, original_code)
