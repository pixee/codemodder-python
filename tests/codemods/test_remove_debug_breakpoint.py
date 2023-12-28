from core_codemods.remove_debug_breakpoint import RemoveDebugBreakpoint
from tests.codemods.base_codemod_test import BaseCodemodTest
from textwrap import dedent


class TestRemoveDebugBreakpoint(BaseCodemodTest):
    codemod = RemoveDebugBreakpoint

    def test_name(self):
        assert self.codemod.name() == "remove-debug-breakpoint"

    def test_builtin_breakpoint(self, tmpdir):
        input_code = """\
        def something():
            var = 1
            breakpoint()
        something()
        """
        expected = """\
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_inline_pdb(self, tmpdir):
        input_code = """\
        def something():
            var = 1
            import pdb; pdb.set_trace()
        something()
        """
        expected = """\
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_pdb_import(self, tmpdir):
        input_code = """\
        import pdb
        def something():
            var = 1
            pdb.set_trace()
        something()
        """
        expected = """\
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_pdb_from_import(self, tmpdir):
        input_code = """\
        from pdb import set_trace()
        def something():
            var = 1
            set_trace()
        something()
        """
        expected = """\
        def something():
            var = 1
        something()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

        # what about line line print(1); breakpoint
