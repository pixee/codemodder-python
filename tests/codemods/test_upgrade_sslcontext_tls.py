import pytest
from codemodder.codemods.upgrade_sslcontext_tls import UpgradeSSLContextTLS
from tests.codemods.base_codemod_test import BaseSemgrepCodemodTest

INSECURE_PROTOCOLS = [
    "PROTOCOL_SSLv2",
    "PROTOCOL_SSLv3",
    "PROTOCOL_TLSv1",
    "PROTOCOL_TLSv1_1",
    "PROTOCOL_TLS",  # This one isn't necessarily insecure, but it is deprecated
]


class TestUpgradeWeakTLS(BaseSemgrepCodemodTest):
    codemod = UpgradeSSLContextTLS

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_with_kwarg(self, tmpdir, protocol):
        input_code = f"""import ssl

context = ssl.SSLContext(protocol=ssl.{protocol})
var = "hello"
"""
        expexted_output = """import ssl

context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_without_kwarg(self, tmpdir, protocol):
        input_code = f"""import ssl

context = ssl.SSLContext(ssl.{protocol})
var = "hello"
"""
        expexted_output = """import ssl

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_outside_sslcontext_dont_update(self, tmpdir, protocol):
        input_code = f"""import ssl

foo(ssl.{protocol})
"""
        expexted_output = input_code

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_outside_call_dont_update(self, tmpdir, protocol):
        input_code = f"""import ssl

if x == ssl.{protocol}:
    print("whatever")
"""
        expexted_output = input_code

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.skip("Need to add support for adding/rewriting imports")
    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_with_kwarg_direct_import(self, tmpdir, protocol):
        input_code = f"""from ssl import {protocol}

context = ssl.SSLContext({protocol})
var = "hello"
"""
        expexted_output = """from ssl import PROTOCOL_TLS_CLIENT

context = ssl.SSLContext(PROTOCOL_TLS_CLIENT)
var = "hello"
"""

        self.run_and_assert(tmpdir, input_code, expexted_output)

    @pytest.mark.parametrize("protocol", INSECURE_PROTOCOLS)
    def test_upgrade_protocol_with_kwarg_import_alias(self, tmpdir, protocol):
        input_code = f"""import ssl as whatever

context = whatever.SSLContext(protocol=whatever.{protocol})
var = "hello"
"""
        expexted_output = """import ssl as whatever

context = whatever.SSLContext(protocol=whatever.PROTOCOL_TLS_CLIENT)
var = "hello"
"""
        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_upgrade_protocol_with_inner_call_do_not_modify(self, tmpdir):
        input_code = """import ssl

ssl.SSLContext(foo(ssl.PROTOCOL_SSLv2))
"""

        expexted_output = input_code

        self.run_and_assert(tmpdir, input_code, expexted_output)

    def test_upgrade_protocol_in_expression_do_not_modify(self, tmpdir):
        input_code = """import ssl

ssl.SSLContext(ssl.PROTOCOL_SSLv2 if condition else ssl.PROTOCOL_TLS_CLIENT)
"""

        expexted_output = input_code

        self.run_and_assert(tmpdir, input_code, expexted_output)
