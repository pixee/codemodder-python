import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.remove_future_imports import DEPRECATED_NAMES, RemoveFutureImports


class TestRemoveFutureImports(BaseCodemodTest):
    codemod = RemoveFutureImports

    @pytest.mark.parametrize("name", DEPRECATED_NAMES)
    def test_remove_future_imports(self, tmpdir, name):
        original_code = f"""
        import os
        from __future__ import {name}
        print("HEY")
        """
        expected_code = """
        import os
        print("HEY")
        """
        self.run_and_assert(tmpdir, original_code, expected_code)

    def test_update_import_star(self, tmpdir):
        original_code = """
        from __future__ import *
        """
        expected_code = """
        from __future__ import annotations
        """
        self.run_and_assert(tmpdir, original_code, expected_code)

    def test_update_import_deprecated_and_annotations(self, tmpdir):
        original_code = """
        from __future__ import print_function, annotations
        """
        expected_code = """
        from __future__ import annotations
        """
        self.run_and_assert(tmpdir, original_code, expected_code)

    def test_not_from_future(self, tmpdir):
        original_code = """
        import os
        from __footure__ import print_function
        print("HEY")
        """
        self.run_and_assert(tmpdir, original_code, original_code)
