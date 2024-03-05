from codemodder.codemods.test import BaseCodemodTest
from core_codemods.remove_debug_breakpoint import RemoveDebugBreakpoint


class TestRemoveDebugBreakpoint(BaseCodemodTest):
    codemod = RemoveDebugBreakpoint

    def test_name(self):
        assert self.codemod.name == "remove-debug-breakpoint"

    def test_builtin_breakpoint(self, tmpdir):
        input_code = """
        def something():
            var = 1
            breakpoint()
        something()
        """
        expected = """
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_builtin_breakpoint_multiple_statements(self, tmpdir):
        input_code = """
        def something():
            var = 1
            print(var); breakpoint()
        something()
        """
        expected = """
        def something():
            var = 1
            print(var); 
        something()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_inline_pdb(self, tmpdir):
        input_code = """
        def something():
            var = 1
            import pdb; pdb.set_trace()
        something()
        """
        expected = """
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_pdb_import(self, tmpdir):
        input_code = """
        import pdb
        def something():
            var = 1
            pdb.set_trace()
        something()
        """
        expected = """
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_pdb_from_import(self, tmpdir):
        input_code = """
        from pdb import set_trace
        def something():
            var = 1
            set_trace()
        something()
        """
        expected = """
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        x = "foo"
        breakpoint()
        """
        lines_to_exclude = [3]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
