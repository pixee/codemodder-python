import pytest
from core_codemods.requests_verify import RequestsVerify
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest

REQUEST_FUNCS = ["get", "post", "request"]


class TestRequestsVerify(BaseSemgrepCodemodTest):
    codemod = RequestsVerify

    def test_name(self):
        assert self.codemod.name() == "requests-verify"

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    def test_default_verify(self, tmpdir, func):
        input_code = f"""import requests

requests.{func}("www.google.com")
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    @pytest.mark.parametrize("verify_val", ["True", "'/some/path'"])
    def test_verify(self, tmpdir, verify_val, func):
        input_code = f"""import requests

requests.{func}("www.google.com", verify={verify_val})
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, input_code)

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    def test_import(self, tmpdir, func):
        input_code = f"""import requests

requests.{func}("www.google.com", verify=False)
var = "hello"
"""
        expected = f"""import requests

requests.{func}("www.google.com", verify=True)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    def test_from_import(self, tmpdir, func):
        input_code = f"""from requests import {func}

{func}("www.google.com", verify=False)
var = "hello"
"""
        expected = f"""from requests import {func}

{func}("www.google.com", verify=True)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    def test_multifunctions(self, tmpdir, func):
        input_code = f"""import requests

requests.{func}("www.google.com", verify=False)
requests.HTTPError()
var = "hello"
"""
        expected = f"""import requests

requests.{func}("www.google.com", verify=True)
requests.HTTPError()
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    def test_import_alias(self, tmpdir, func):
        input_code = f"""import requests as req_mod

req_mod.{func}("www.google.com", verify=False)
var = "hello"
"""
        expected = f"""import requests as req_mod

req_mod.{func}("www.google.com", verify=True)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize("func", REQUEST_FUNCS)
    def test_multiple_kwargs(self, tmpdir, func):
        input_code = f"""import requests

requests.{func}("www.google.com", headers={{"Content-Type":"text"}}, verify=False)
var = "hello"
"""
        expected = f"""import requests

requests.{func}("www.google.com", headers={{"Content-Type":"text"}}, verify=True)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected)
