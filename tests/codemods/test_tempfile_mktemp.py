from core_codemods.tempfile_mktemp import TempfileMktemp
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestTempfileMktemp(BaseSemgrepCodemodTest):
    codemod = TempfileMktemp

    def test_name(self):
        assert self.codemod.name() == "secure-tempfile"

    def test_import(self, tmpdir):
        input_code = """import tempfile

tempfile.mktemp()
var = "hello"
"""
        expected_output = """import tempfile

tempfile.mkstemp()
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_with_arg(self, tmpdir):
        input_code = """import tempfile

tempfile.mktemp('something')
var = "hello"
"""
        expected_output = """import tempfile

tempfile.mkstemp('something')
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_from_import(self, tmpdir):
        input_code = """from tempfile import mktemp

mktemp()
var = "hello"
"""
        expected_output = """import tempfile

tempfile.mkstemp()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_alias(self, tmpdir):
        input_code = """import tempfile as _tempfile

_tempfile.mktemp()
var = "hello"
"""
        expected_output = """import tempfile as _tempfile

_tempfile.mkstemp()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_method_alias(self, tmpdir):
        input_code = """from tempfile import mktemp as get_temp_file

get_temp_file()
var = "hello"
"""
        expected_output = """import tempfile

tempfile.mkstemp()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_random_multifunctions(self, tmpdir):
        input_code = """from tempfile import mktemp, TemporaryFile

mktemp()
TemporaryFile()
var = "hello"
"""
        expected_output = """from tempfile import TemporaryFile
import tempfile

tempfile.mkstemp()
TemporaryFile()
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)
