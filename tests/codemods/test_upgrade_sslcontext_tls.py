import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.upgrade_sslcontext_tls import UpgradeSSLContextTLS

INSECURE_PROTOCOLS = [
    "PROTOCOL_SSLv2",
    "PROTOCOL_SSLv3",
    "PROTOCOL_TLSv1",
    "PROTOCOL_TLSv1_1",
    "PROTOCOL_TLS",  # This one isn't necessarily insecure, but it is deprecated
]


class TestUpgradeWeakTLS(BaseCodemodTest):
    codemod = UpgradeSSLContextTLS

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_with_kwarg(self, tmpdir, protocol):
        input_code = f"""import ssl

context = ssl.SSLContext(protocol=ssl.{protocol})
var = "hello"
"""
        expected_output = """import ssl

context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_without_kwarg(self, tmpdir, protocol):
        input_code = f"""import ssl

context = ssl.SSLContext(ssl.{protocol})
var = "hello"
"""
        expected_output = """import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_outside_sslcontext_dont_update(self, tmpdir, protocol):
        input_code = f"""import ssl

foo(ssl.{protocol})
"""
        expected_output = input_code

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_outside_call_dont_update(self, tmpdir, protocol):
        input_code = f"""import ssl

if x == ssl.{protocol}:
    print("whatever")
"""
        expected_output = input_code

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.skip("Need to add support for adding/rewriting imports")
    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_with_kwarg_direct_import(self, tmpdir, protocol):
        input_code = f"""from ssl import {protocol}

context = ssl.SSLContext({protocol})
var = "hello"
"""
        expected_output = """from ssl import PROTOCOL_TLS_CLIENT

context = ssl.SSLContext(PROTOCOL_TLS_CLIENT)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expected_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_with_kwarg_import_alias(self, tmpdir, protocol):
        input_code = f"""import ssl as whatever

context = whatever.SSLContext(protocol=whatever.{protocol})
var = "hello"
"""
        expected_output = """import ssl as whatever
import ssl

context = whatever.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_upgrade_protocol_with_inner_call_do_not_modify(self, tmpdir):
        input_code = """import ssl

ssl.SSLContext(foo(ssl.PROTOCOL_SSLv2))
"""

        expected_output = input_code

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_upgrade_protocol_in_expression_do_not_modify(self, tmpdir):
        input_code = """import ssl

ssl.SSLContext(ssl.PROTOCOL_SSLv2 if condition else ssl.PROTOCOL_TLS_CLIENT)
"""

        expected_output = input_code

        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_import_no_protocol(self, tmpdir):
        input_code = """import ssl
context = ssl.SSLContext()
"""
        expected_output = """import ssl
context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)

    def test_from_import_no_protocol(self, tmpdir):
        input_code = """from ssl import SSLContext
SSLContext()
"""
        expected_output = """from ssl import SSLContext
import ssl

SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
"""
        self.run_and_assert(tmpdir, input_code, expected_output)
