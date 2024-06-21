from codemodder.codemods.test import BaseCodemodTest
from core_codemods.limit_readline import LimitReadline


class TestLimitReadline(BaseCodemodTest):
    codemod = LimitReadline

    def test_name(self):
        assert self.codemod.name == "limit-readline"

    def test_file_readline(self, tmpdir):
        input_code = """file = open('some_file.txt')
file.readline()
"""
        expected = """file = open('some_file.txt')
file.readline(5_000_000)
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_StringIO_readline(self, tmpdir):
        input_code = """import io
io.StringIO('some_string').readline()
"""

        expected = """import io
io.StringIO('some_string').readline(5_000_000)
"""

        self.run_and_assert(tmpdir, input_code, expected)

    def test_BytesIO_readline(self, tmpdir):
        input_code = """import io
io.BytesIO(b'some_string').readline()
"""

        expected = """import io
io.BytesIO(b'some_string').readline(5_000_000)
"""

        self.run_and_assert(tmpdir, input_code, expected)

    def test_taint_tracking(self, tmpdir):
        input_code = """file = open('some_file.txt')
arg = file
arg.readline(5_000_000)
"""

        expected = """file = open('some_file.txt')
arg = file
arg.readline(5_000_000)
"""

        self.run_and_assert(tmpdir, input_code, expected)
