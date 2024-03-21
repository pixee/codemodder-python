from codemodder.codemods.test import BaseIntegrationTest
from core_codemods.fix_mutable_params import (
    FixMutableParams,
    FixMutableParamsTransformer,
)


class TestFixMutableParams(BaseIntegrationTest):
    codemod = FixMutableParams
    original_code = """
    def foo(x, y=[]):
        y.append(x)
        print(y)
    
    
    def bar(x="hello"):
        print(x)
    
    
    def baz(x={"foo": 42}, y=set()):
        print(x)
        print(y)
    """
    expected_new_code = """
    def foo(x, y=None):
        y = [] if y is None else y
        y.append(x)
        print(y)
    
    
    def bar(x="hello"):
        print(x)
    
    
    def baz(x=None, y=None):
        x = {"foo": 42} if x is None else x
        y = set() if y is None else y
        print(x)
        print(y)
    """

    expected_diff = '--- \n+++ \n@@ -1,4 +1,5 @@\n-def foo(x, y=[]):\n+def foo(x, y=None):\n+    y = [] if y is None else y\n     y.append(x)\n     print(y)\n \n@@ -7,6 +8,8 @@\n     print(x)\n \n \n-def baz(x={"foo": 42}, y=set()):\n+def baz(x=None, y=None):\n+    x = {"foo": 42} if x is None else x\n+    y = set() if y is None else y\n     print(x)\n     print(y)'
    expected_line_change = 1
    num_changes = 2
    change_description = FixMutableParamsTransformer.change_description
