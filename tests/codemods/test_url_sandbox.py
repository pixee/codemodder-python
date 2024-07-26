import mock
import pytest

from codemodder.codemods.test import BaseCodemodTest
from codemodder.dependency import Security
from core_codemods.url_sandbox import UrlSandbox


@mock.patch("codemodder.codemods.api.FileContext.add_dependency")
class TestUrlSandbox(BaseCodemodTest):
    codemod = UrlSandbox

    def test_name(self, _):
        assert self.codemod.name == "url-sandbox"

    def test_import_requests(self, add_dependency, tmpdir):
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
        add_dependency.assert_called_once_with(Security)

    def test_from_requests(self, add_dependency, tmpdir):
        input_code = """
        from requests import get

        url = input()
        get(url)
        var = "hello"
        """
        expected = """
        from security import safe_requests

        url = input()
        safe_requests.get(url)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        add_dependency.assert_called_once_with(Security)

    def test_requests_nameerror(self, _, tmpdir):
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
    def test_requests_other_import_untouched(
        self, add_dependency, tmpdir, input_code, expected
    ):
        self.run_and_assert(tmpdir, input_code, expected)
        add_dependency.assert_called_once_with(Security)

    def test_requests_multifunctions(self, add_dependency, tmpdir):
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
        add_dependency.assert_called_once_with(Security)

    def test_custom_get(self, _, tmpdir):
        input_code = """
        from app_funcs import get

        url = input()
        get(url)
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_ambiguous_get(self, _, tmpdir):
        input_code = """
        from requests import get

        def get(url):
            pass

        url = input()
        get(url)
        """
        expected = input_code
        self.run_and_assert(tmpdir, input_code, expected)

    def test_from_requests_with_alias(self, add_dependency, tmpdir):
        input_code = """
        from requests import get as got

        url = input()
        got(url)
        var = "hello"
        """
        expected = """
        from security import safe_requests

        url = input()
        safe_requests.get(url)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
        add_dependency.assert_called_once_with(Security)

    def test_requests_with_alias(self, add_dependency, tmpdir):
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
        add_dependency.assert_called_once_with(Security)

    def test_ignore_hardcoded(self, _, tmpdir):
        expected = (
            input_code
        ) = """
        import requests

        requests.get("www.google.com")
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_but_not_all(self, _, tmpdir):
        input_code = """
        import requests

        requests.get("www.google.com")
        url = input()
        requests.get(url)
        """
        expected = """
        import requests
        from security import safe_requests

        requests.get("www.google.com")
        url = input()
        safe_requests.get(url)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_global_variable(self, _, tmpdir):
        expected = (
            input_code
        ) = """
        import requests

        URL = "www.google.com"
        requests.get(URL)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_local_variable(self, _, tmpdir):
        expected = (
            input_code
        ) = """
        import requests

        def foo():
            url = "www.google.com"
            requests.get(url)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_local_variable_transitive(self, _, tmpdir):
        expected = (
            input_code
        ) = """
        import requests

        def foo():
            url = "www.google.com"
            new_url = url
            requests.get(new_url)
        """

        self.run_and_assert(tmpdir, input_code, expected)

    def test_ignore_hardcoded_from_local_variable_transitive_reassigned(
        self, _, tmpdir
    ):
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

    def test_multiple_imports(self, add_dependency, tmpdir):
        input_code = """
        from requests import Response, Timeout, get
        import csv

        del Response, Timeout # just to make sure these names are used

        url = input()
        get(url)
        csv.excel
        """
        expected = """
        from requests import Response, Timeout
        import csv
        from security import safe_requests

        del Response, Timeout # just to make sure these names are used

        url = input()
        safe_requests.get(url)
        csv.excel
        """
        self.run_and_assert(tmpdir, input_code, expected)
        add_dependency.assert_called_once_with(Security)
