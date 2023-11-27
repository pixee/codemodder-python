from tests.codemods.base_codemod_test import BaseCodemodTest
from core_codemods.file_resource_leak import FileResourceLeak
from textwrap import dedent


class TestFileResourceLeak(BaseCodemodTest):
    codemod = FileResourceLeak

    def test_name(self):
        assert self.codemod.name() == "fix-file-resource-leak"

    def test_simple(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        file.read()
        """
        expected = """\
        with open('test.txt', 'r') as file:
            file.read()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_simple_annotated(self, tmpdir):
        input_code = """\
        file: int = open('test.txt', 'r')
        file.read()
        """
        expected = """\
        with open('test.txt', 'r') as file:
            file.read()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_just_open(self, tmpdir):
        # strange as this change may be, it still leaks if left untouched
        input_code = """\
        file = open('test.txt', 'r')
        """
        expected = """\
        with open('test.txt', 'r') as file:
            pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_multiple_assignments(self, tmpdir):
        input_code = """\
        file = file2 = open('test.txt', 'r')
        file.read()
        """
        expected = """\
        with open('test.txt', 'r') as file, file as file2:
            file.read()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    def test_minimal_block(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        file.read()
        pass
        """
        expected = """\
        with open('test.txt', 'r') as file:
            file.read()
        pass
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(expected))
        assert len(self.file_context.codemod_changes) == 1

    # negative tests below

    def test_is_closed(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        file.read()
        file.close()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_is_closed_with_exit(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        file.read()
        file.__exit__()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_is_closed_with_statement(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        with file:
            file.read()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_is_closed_with_statement_and_contextlib(self, tmpdir):
        input_code = """\
        import contextlib
        file = open('test.txt', 'r')
        with contextlib.closing(file):
            file.read()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_is_closed_transitivelly(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        same_file = file
        same_file.close()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_escapes_with_assignment(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        Object.attribute = file
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_escapes_as_function_argument(self, tmpdir):
        input_code = """\
        file = open('test.txt', 'r')
        foo(file)
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_escapes_returned(self, tmpdir):
        input_code = """\
        def foo():
            file = open('test.txt', 'r')
            return file
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_escapes_yielded(self, tmpdir):
        input_code = """\
        def foo():
            file = open('test.txt', 'r')
            yield file
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0

    def test_escapes_outside_reference(self, tmpdir):
        input_code = """\
        out = None
        if True:
            file = open('test.txt', 'r')
            out = file
            file.read()
        out.read()
        """
        self.run_and_assert(tmpdir, dedent(input_code), dedent(input_code))
        assert len(self.file_context.codemod_changes) == 0
