from collections import defaultdict
from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
import pytest
from codemodder.codemods.url_sandbox import UrlSandbox
from codemodder.file_context import FileContext
from codemodder.semgrep import run_on_directory as semgrep_run
from codemodder.semgrep import find_all_yaml_files


class TestUrlSandbox:
    def results_by_id(self, input_code, tmpdir):
        tmp_file_path = tmpdir / "code.py"
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(input_code)

        return semgrep_run(
            find_all_yaml_files({UrlSandbox.METADATA.NAME: UrlSandbox}), tmpdir
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
        command_instance = UrlSandbox(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == expected

    def test_with_empty_results(self):
        input_code = """import requests

requests.get("www.google.com")
var = "hello"
"""
        input_tree = cst.parse_module(input_code)
        file_context = FileContext(Path(""), False, [], [], defaultdict(list))
        command_instance = UrlSandbox(CodemodContext(), file_context)
        output_tree = command_instance.transform_module(input_tree)

        assert output_tree.code == input_code

    def test_import_requests(self, tmpdir):
        input_code = """import requests

requests.get("www.google.com")
var = "hello"
"""
        expected = """from security import safe_requests

safe_requests.get("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_rule_ids(self):
        assert UrlSandbox.RULE_IDS == ["sandbox-url-creation"]

    def test_from_requests(self, tmpdir):
        input_code = """from requests import get

get("www.google.com")
var = "hello"
"""
        expected = """from security.safe_requests import get

get("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_requests_nameerror(self, tmpdir):
        input_code = """requests.get("www.google.com")

import requests
"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "input_code,expected",
        [
            (
                """import requests
import csv
requests.get("www.google.com")
csv.excel
""",
                """import csv
from security import safe_requests

safe_requests.get("www.google.com")
csv.excel
""",
            ),
            (
                """import requests
from csv import excel
requests.get("www.google.com")
excel
""",
                """from csv import excel
from security import safe_requests

safe_requests.get("www.google.com")
excel
""",
            ),
        ],
    )
    def test_requests_other_import_untouched(self, tmpdir, input_code, expected):
        self.run_and_assert(tmpdir, input_code, expected)

    def test_requests_multifunctions(self, tmpdir):
        # Test that `requests` import isn't removed if code uses part of the requests
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """import requests

requests.get("www.google.com")
requests.status_codes.codes.FORBIDDEN
        """

        expected = """import requests
from security import safe_requests

safe_requests.get("www.google.com")
requests.status_codes.codes.FORBIDDEN"""

        self.run_and_assert(tmpdir, input_code, expected)

    def test_custom_get(self, tmpdir):
        input_code = """from app_funcs import get

get("www.google.com")"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_ambiguous_get(self, tmpdir):
        input_code = """from requests import get

def get(url):
    pass

get("www.google.com")"""
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_requests_with_alias(self, tmpdir):
        input_code = """from requests import get as got

got("www.google.com")
var = "hello"
"""
        expected = """from security.safe_requests import get as got

got("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    def test_requests_with_alias(self, tmpdir):
        input_code = """import requests as req

req.get("www.google.com")
var = "hello"
"""
        expected = """from security import safe_requests

safe_requests.get("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)
