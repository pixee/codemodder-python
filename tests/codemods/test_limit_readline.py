from collections import defaultdict
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.codemods.limit_readline import LimitReadline
from codemodder.file_context import FileContext
from codemodder.semgrep import run_on_directory as semgrep_run
from codemodder.semgrep import find_all_yaml_files


class TestLimitReadline:
    def results_by_id(self, input_code, tmpdir):
        tmp_file_path = tmpdir / "code.py"
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        return semgrep_run(
            find_all_yaml_files({LimitReadline.METADATA.NAME: LimitReadline}), tmpdir
        )

    def run_and_assert(self, tmpdir, input_code, expected):
        input_tree = cst.parse_module(input_code)
        results = self.results_by_id(input_code, tmpdir)[tmpdir / "code.py"]
        file_context = FileContext(
            tmpdir / "code.py",
            False,
            [],
            [],
            results,
        )
        command_instance = LimitReadline(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def test_rule_ids(self):
        assert LimitReadline.RULE_IDS == ["limit-readline"]

    def test_with_empty_results(self):
        input_code = """file = open('some_file.txt')
file.readline()
"""
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(Path(""), False, [], [], defaultdict(list))
        command_instance = LimitReadline(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == input_code

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
