import pytest

from core_codemods.add_requests_timeouts import AddRequestsTimeouts
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest

METHODS = ["get", "post", "put", "delete", "head", "options", "patch"]
TIMEOUT = AddRequestsTimeouts.DEFAULT_TIMEOUT


class TestAddRequestsTimeouts(BaseSemgrepCodemodTest):
    codemod = AddRequestsTimeouts

    @pytest.mark.parametrize("method", METHODS)
    def test_import(self, tmpdir, method):
        original = f"""
            import requests
            requests.{method}("https://example.com")
        """
        expected = f"""
            import requests
            requests.{method}("https://example.com", timeout={TIMEOUT})
        """
        self.run_and_assert(tmpdir, original, expected)

    def test_import_use_request(self, tmpdir):
        original = """
            import requests
            requests.request("GET", "https://example.com")
        """
        expected = f"""
            import requests
            requests.request("GET", "https://example.com", timeout={TIMEOUT})
        """
        self.run_and_assert(tmpdir, original, expected)

    @pytest.mark.parametrize("method", METHODS)
    def test_import_from(self, tmpdir, method):
        original = f"""
            from requests import {method}
            {method}("https://example.com")
        """
        expected = f"""
            from requests import {method}
            {method}("https://example.com", timeout={TIMEOUT})
        """
        self.run_and_assert(tmpdir, original, expected)

    @pytest.mark.parametrize("method", METHODS)
    def test_import_alias(self, tmpdir, method):
        original = f"""
            from requests import {method} as my_method
            my_method("https://example.com")
        """
        expected = f"""
            from requests import {method} as my_method
            my_method("https://example.com", timeout={TIMEOUT})
        """
        self.run_and_assert(tmpdir, original, expected)

    def test_preserve_other_args(self, tmpdir):
        original = """
            import requests
            requests.get("https://example.com", headers={"foo": "bar"})
        """
        expected = f"""
            import requests
            requests.get("https://example.com", headers={{"foo": "bar"}}, timeout={TIMEOUT})
        """
        self.run_and_assert(tmpdir, original, expected)

    def test_has_timeout(self, tmpdir):
        original = """
            import requests
            requests.get("https://example.com", timeout=10)
        """
        self.run_and_assert(tmpdir, original, original)

    def test_not_requests(self, tmpdir):
        original = """
            import demands
            demands.get("https://example.com")
        """
        self.run_and_assert(tmpdir, original, original)
