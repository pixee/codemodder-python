from textwrap import dedent

from core_codemods.fix_deprecated_abstractproperty import FixDeprecatedAbstractproperty
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestFixDeprecatedAbstractproperty(BaseIntegrationTest):
    codemod = FixDeprecatedAbstractproperty
    code_path = "tests/samples/deprecated_abstractproperty.py"

    original_code, _ = original_and_expected_from_code_path(code_path, [])
    expected_new_code = dedent(
        """\
    from abc import abstractmethod
    import abc


    class A:
        @property
        @abc.abstractmethod
        def foo(self):
            pass

        @abstractmethod
        def bar(self):
            pass
    """
    )

    expected_diff = """\
--- 
+++ 
@@ -1,8 +1,10 @@
-from abc import abstractproperty as ap, abstractmethod
+from abc import abstractmethod
+import abc
 
 
 class A:
-    @ap
+    @property
+    @abc.abstractmethod
     def foo(self):
         pass
 
"""

    expected_line_change = "5"
    change_description = FixDeprecatedAbstractproperty.DESCRIPTION
