from codemodder.codemods.test import BaseCodemodTest
from core_codemods.https_connection import HTTPSConnection


class TestHTTPSConnection(BaseCodemodTest):
    codemod = HTTPSConnection

    def test_no_change(self, tmpdir):
        before = r"""import urllib3

urllib3.HTTPSConnectionPool("localhost", "80")
"""
        self.run_and_assert(tmpdir, before, before)

    def test_simple(self, tmpdir):
        before = r"""import urllib3

urllib3.HTTPConnectionPool("localhost", "80")
"""
        after = r"""import urllib3

urllib3.HTTPSConnectionPool("localhost", "80")
"""
        self.run_and_assert(tmpdir, before, after)

    def test_module_alias(self, tmpdir):
        before = r"""import urllib3 as module

module.HTTPConnectionPool("localhost", "80")
"""
        after = r"""import urllib3 as module

module.HTTPSConnectionPool("localhost", "80")
"""
        self.run_and_assert(tmpdir, before, after)

    def test_alias(self, tmpdir):
        before = r"""from urllib3 import HTTPConnectionPool as something

something("localhost", "80")
"""
        after = r"""import urllib3

urllib3.HTTPSConnectionPool("localhost", "80")
"""
        self.run_and_assert(tmpdir, before, after)

    def test_connectionpool(self, tmpdir):
        before = r"""import urllib3

urllib3.connectionpool.HTTPConnectionPool("localhost", "80")
"""
        after = r"""import urllib3

urllib3.connectionpool.HTTPSConnectionPool("localhost", "80")
"""
        self.run_and_assert(tmpdir, before, after)

    def test_connectionpool_alias(self, tmpdir):
        before = r"""import urllib3.connectionpool as pool

pool.HTTPConnectionPool("localhost", "80")
"""
        after = r"""import urllib3.connectionpool as pool

pool.HTTPSConnectionPool("localhost", "80")
"""
        self.run_and_assert(tmpdir, before, after)

    def test_last_arg(self, tmpdir):
        before = r"""import urllib3

urllib3.HTTPConnectionPool(None, None, None, None, None, None, None, None, None, None)
"""
        after = r"""import urllib3

urllib3.HTTPSConnectionPool(None, None, None, None, None, None, None, None, None, _proxy_config = None)
"""
        self.run_and_assert(tmpdir, before, after)
