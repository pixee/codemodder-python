from codemodder.codemods.test import BaseCodemodTest
from core_codemods.file_resource_leak import FileResourceLeak


class TestFileResourceLeak(BaseCodemodTest):
    codemod = FileResourceLeak

    def test_name(self):
        assert self.codemod.name == "fix-file-resource-leak"

    def test_simple(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        file.read()
        """
        expected = """
        with open('test.txt', 'r') as file:
            file.read()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_unused(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        """
        expected = """
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_unused_inside_block(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        file2 = open('test2.txt','r')
        file.read()
        """
        expected = """
        with open('test.txt', 'r') as file:
            file.read()
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=2)

    def test_simple_annotated(self, tmpdir):
        input_code = """
        file: int = open('test.txt', 'r')
        file.read()
        """
        expected = """
        with open('test.txt', 'r') as file:
            file.read()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_multiple_in_block(self, tmpdir):
        input_code = """\
        def foo():
            si = open('/dev/null', 'r')
            so = open('/dev/null', 'a+')
            se = open('/dev/null', 'w+')
            def foo():
                f = open('test')
                f.read()
            si.read()
            se.read()
            so.read()
            print('stop')
        """
        expected = """\
        def foo():
            with open('/dev/null', 'r') as si:
                with open('/dev/null', 'a+') as so:
                    with open('/dev/null', 'w+') as se:
                        def foo():
                            with open('test') as f:
                                f.read()
                        si.read()
                        se.read()
                    so.read()
            print('stop')
        """
        self.run_and_assert(tmpdir, input_code, expected, num_changes=4)

    def test_multiple_assignments(self, tmpdir):
        input_code = """
        file = file2 = open('test.txt', 'r')
        file.read()
        """
        expected = """
        with open('test.txt', 'r') as file, file as file2:
            file.read()
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_minimal_block(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        file.read()
        pass
        """
        expected = """
        with open('test.txt', 'r') as file:
            file.read()
        pass
        """
        self.run_and_assert(tmpdir, input_code, expected)

    # negative tests below

    def test_is_closed(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        file.read()
        file.close()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_is_closed_with_exit(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        file.read()
        file.__exit__()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_is_closed_with_statement(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        with file:
            file.read()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_is_closed_with_statement_and_contextlib(self, tmpdir):
        input_code = """
        import contextlib
        file = open('test.txt', 'r')
        with contextlib.closing(file):
            file.read()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_is_closed_transitivelly(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        same_file = file
        same_file.close()
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_escapes_with_assignment(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        Object.attribute = file
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_escapes_as_function_argument(self, tmpdir):
        input_code = """
        file = open('test.txt', 'r')
        foo(file)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_escapes_returned(self, tmpdir):
        input_code = """
        def foo():
            file = open('test.txt', 'r')
            return file
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_escapes_yielded(self, tmpdir):
        input_code = """
        def foo():
            file = open('test.txt', 'r')
            yield file
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_escapes_outside_reference(self, tmpdir):
        input_code = """
        out = None
        if True:
            file = open('test.txt', 'r')
            out = file
            file.read()
        out.read()
        """
        self.run_and_assert(tmpdir, input_code, input_code)
