import pytest
from core_codemods.tempfile_mktemp import TempfileMktemp
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestTempfileMktemp(BaseSemgrepCodemodTest):
    codemod = TempfileMktemp

    def test_rule_ids(self):
        assert self.codemod.RULE_IDS == ["secure-tempfile"]

    def test_import(self, tmpdir):
        input_code = """import tempfile

tempfile.mktemp()
var = "hello"
"""
        expexted_output = """import tempfile

tempfile.mkstemp()
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_import_with_arg(self, tmpdir):
        input_code = """import tempfile

tempfile.mktemp('something')
var = "hello"
"""
        expexted_output = """import tempfile

tempfile.mkstemp('something')
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_from_import(self, tmpdir):
        input_code = """from tempfile import mktemp

mktemp()
var = "hello"
"""
        expexted_output = """import tempfile

tempfile.mkstemp()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.skip()
    def test_import_alias(self, tmpdir):
        input_code = """import tempfile as _tempfile

_tempfile.mktemp()
var = "hello"
"""
        expexted_output = """import tempfile as _tempfile

_tempfile.mkstemp()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_random_multifunctions(self, tmpdir):
        input_code = """from tempfile import mktemp, TemporaryFile

mktemp()
TemporaryFile()
var = "hello"
"""
        expexted_output = """from tempfile import TemporaryFile
import tempfile

tempfile.mkstemp()
TemporaryFile()
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)
