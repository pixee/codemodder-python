import pytest

from codemodder.dependency import Security
from core_codemods.url_sandbox import UrlSandbox
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest


class TestUrlSandbox(BaseSemgrepCodemodTest):
    codemod = UrlSandbox

    def test_name(self):
        assert self.codemod.name() == "url-sandbox"

    def test_import_requests(self, tmpdir):
        input_code = """
        import requests

        url = input()
        requests.get(url)
        var = "hello"
        """
        expected = """
        from security import safe_requests

        url = input()
        safe_requests.get(url)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        self.assert_dependency(Security)

    def test_from_requests(self, tmpdir):
        input_code = """
        from requests import get

        url = input()
        get(url)
        var = "hello"
        """
        expected = """
        from security.safe_requests import get

        url = input()
        get(url)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        self.assert_dependency(Security)

    def test_requests_nameerror(self, tmpdir):
        input_code = """
        url = input()
        requests.get(url)

        import requests
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "input_code,expected",
        [
            (
                """
                import requests
                import csv
                url = input()
                requests.get(url)
                csv.excel
                """,
                """
                import csv
                from security import safe_requests

                url = input()
                safe_requests.get(url)
                csv.excel
                """,
            ),
            (
                """
                import requests
                from csv import excel
                url = input()
                requests.get(url)
                excel
                """,
                """
                from csv import excel
                from security import safe_requests

                url = input()
                safe_requests.get(url)
                excel
                """,
            ),
        ],
    )
    def test_requests_other_import_untouched(self, tmpdir, input_code, expected):
        self.run_and_assert(tmpdir, input_code, expected)
        self.assert_dependency(Security)

    def test_requests_multifunctions(self, tmpdir):
        # Test that `requests` import isn't removed if code uses part of the requests
        # library that isn't part of our codemods. If we add the function as one of
        # our codemods, this test would change.
        input_code = """
        import requests

        url = input()
        requests.get(url)
        requests.status_codes.codes.FORBIDDEN
        """

        expected = """
        import requests
        from security import safe_requests

        url = input()
        safe_requests.get(url)
        requests.status_codes.codes.FORBIDDEN
        """

        self.run_and_assert(tmpdir, input_code, expected)
        self.assert_dependency(Security)

    def test_custom_get(self, tmpdir):
        input_code = """
        from app_funcs import get

        url = input()
        get(url)
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_ambiguous_get(self, tmpdir):
        input_code = """
        from requests import get

        def get(url):
            pass

        url = input()
        get(url)
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_requests_with_alias(self, tmpdir):
        input_code = """
        from requests import get as got

        url = input()
        got(url)
        var = "hello"
        """
        expected = """
        from security.safe_requests import get as got

        url = input()
        got(url)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        self.assert_dependency(Security)

    def test_requests_with_alias(self, tmpdir):
        input_code = """
        import requests as req

        url = input()
        req.get(url)
        var = "hello"
        """
        expected = """
        from security import safe_requests

        url = input()
        safe_requests.get(url)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        self.assert_dependency(Security)

    def test_ignore_hardcoded(self, tmpdir):
        expected = input_code = """
        import requests

        requests.get("www.google.com")
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_global_variable(self, tmpdir):
        expected = input_code = """
        import requests

        URL = "www.google.com"
        requests.get(URL)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_local_variable(self, tmpdir):
        expected = input_code = """
        import requests

        def foo():
            url = "www.google.com"
            requests.get(url)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_local_variable_transitive(self, tmpdir):
        expected = input_code = """
        import requests

        def foo():
            url = "www.google.com"
            new_url = url
            requests.get(new_url)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_local_variable_transitive_reassigned(self, tmpdir):
        input_code = """
        import requests

        def foo():
            url = "www.google.com"
            new_url = url
            new_url = input()
            requests.get(new_url)
        """

        expected = """
        from security import safe_requests

        def foo():
            url = "www.google.com"
            new_url = url
            new_url = input()
            safe_requests.get(new_url)
        """

        self.run_and_assert(tmpdir, input_code, expected)
