import pytest
from core_codemods.requests_verify import RequestsVerify
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest

# todo: add stream, etc specific to httpx
each_func = pytest.mark.parametrize("func", ["get", "post", "request"])
each_library = pytest.mark.parametrize("library", ["requests", "httpx"])


class TestRequestsVerify(BaseSemgrepCodemodTest):
    codemod = RequestsVerify

    def test_name(self):
        assert self.codemod.name == "requests-verify"

    @each_func
    @each_library
    def test_default_verify(self, tmpdir, library, func):
        input_code = f"""
        import {library}
        {library}.{func}("www.google.com")
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @each_func
    @each_library
    @pytest.mark.parametrize("verify_val", ["True", "'/some/palibrary, th'"])
    def test_verify(self, tmpdir, verify_val, library, func):
        input_code = f"""
        import {library}
        {library}.{func}("www.google.com", verify={verify_val})
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    @each_func
    @each_library
    def test_import(self, tmpdir, library, func):
        input_code = f"""
        import {library}
        {library}.{func}("www.google.com", verify=False)
        var = "hello"
        """
        expected = f"""
        import {library}
        {library}.{func}("www.google.com", verify=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @each_func
    @each_library
    def test_from_import(self, tmpdir, library, func):
        input_code = f"""
        from {library} import {func}
        {func}("www.google.com", verify=False)
        var = "hello"
        """
        expected = f"""
        from {library} import {func}
        {func}("www.google.com", verify=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @each_func
    @each_library
    def test_multifunctions(self, tmpdir, library, func):
        input_code = f"""
        import {library}
        {library}.{func}("www.google.com", verify=False)
        {library}.HTTPError()
        var = "hello"
        """
        expected = f"""
        import {library}
        {library}.{func}("www.google.com", verify=True)
        {library}.HTTPError()
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @each_func
    @each_library
    def test_import_alias(self, tmpdir, library, func):
        input_code = f"""
        import {library} as req_mod
        req_mod.{func}("www.google.com", verify=False)
        var = "hello"
        """
        expected = f"""
        import {library} as req_mod
        req_mod.{func}("www.google.com", verify=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)

    @each_func
    @each_library
    def test_multiple_kwargs(self, tmpdir, library, func):
        input_code = f"""
        import {library}
        {library}.{func}("www.google.com", headers={{"Content-Type":"text"}}, verify=False)
        var = "hello"
        """
        expected = f"""
        import {library}
        {library}.{func}("www.google.com", headers={{"Content-Type":"text"}}, verify=True)
        var = "hello"
        """
        self.run_and_assert(tmpdir, input_code, expected)
