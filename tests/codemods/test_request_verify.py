import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.requests_verify import RequestsVerify

each_func = pytest.mark.parametrize("func", ["get", "post", "request"])
each_library = pytest.mark.parametrize("library", ["requests", "httpx"])


class TestRequestsVerify(BaseCodemodTest):
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
    @pytest.mark.parametrize("verify_val", ["True", "'/some/path'"])
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


class TestHttpxSpecific(BaseCodemodTest):
    codemod = RequestsVerify

    def test_stream(self, tmpdir):
        input_code = """
        import httpx
        with httpx.stream("GET", "https://www.example.com", verify=False) as r:
            for data in r.iter_bytes():
                print(data)
        """
        expected = """
        import httpx
        with httpx.stream("GET", "https://www.example.com", verify=True) as r:
            for data in r.iter_bytes():
                print(data)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_stream_from_import(self, tmpdir):
        input_code = """
        from httpx import stream
        with stream("GET", "https://www.example.com", verify=False) as r:
            for data in r.iter_bytes():
                print(data)
        """
        expected = """
        from httpx import stream
        with stream("GET", "https://www.example.com", verify=True) as r:
            for data in r.iter_bytes():
                print(data)
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_verify_with_sslcontext(self, tmpdir):
        input_code = """
        import ssl
        import httpx
        context = ssl.create_default_context()
        context.load_verify_locations(cafile="/tmp/temp.pem")
        httpx.get('https://google.com', verify=context)
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_client_verify(self, tmpdir):
        input_code = """
        import httpx
        client = httpx.Client(verify=False)
        try:
            client.get('https://example.com')
        finally:
            client.close()
        """
        expected_code = """
        import httpx
        client = httpx.Client(verify=True)
        try:
            client.get('https://example.com')
        finally:
            client.close()
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_client_verify_from_import(self, tmpdir):
        input_code = """
        from httpx import Client
        c = Client(verify=False)
        try:
            c.get('https://example.com')
        finally:
            c.close()
        """
        expected_code = """
        from httpx import Client
        c = Client(verify=True)
        try:
            c.get('https://example.com')
        finally:
            c.close()
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_client_verify_context_manager(self, tmpdir):
        input_code = """
        import httpx
        with httpx.Client(verify=False) as client:
            client.get('https://example.com')
        """
        expected_code = """
        import httpx
        with httpx.Client(verify=True) as client:
            client.get('https://example.com')
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_async_client_verify(self, tmpdir):
        input_code = """
        import httpx
        client = httpx.AsyncClient(verify=False)
        try:
            await client.get('https://example.com')
        finally:
            await client.close()
        """
        expected_code = """
        import httpx
        client = httpx.AsyncClient(verify=True)
        try:
            await client.get('https://example.com')
        finally:
            await client.close()
        """
        self.run_and_assert(tmpdir, input_code, expected_code)

    def test_async_client_verify_context_manager(self, tmpdir):
        input_code = """
        import httpx
        async with httpx.AsyncClient(verify=False) as client:
            await client.get('https://example.com')
        """
        expected_code = """
        import httpx
        async with httpx.AsyncClient(verify=True) as client:
            await client.get('https://example.com')
        """
        self.run_and_assert(tmpdir, input_code, expected_code)
