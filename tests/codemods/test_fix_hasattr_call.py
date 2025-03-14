from codemodder.codemods.test import BaseCodemodTest
from core_codemods.fix_hasattr_call import TransformFixHasattrCall


class TestTransformFixHasattrCall(BaseCodemodTest):
    codemod = TransformFixHasattrCall

    def test_name(self):
        assert self.codemod.name == "fix-hasattr-call"

    def test_combine(self, tmpdir):
        input_code = """
        class Test:
            pass

        hasattr(Test(), "__call__")
        hasattr("hi", '__call__')
        
        assert hasattr(1, '__call__')
        obj = Test()
        var = hasattr(obj, "__call__")
        
        if hasattr(obj, "__call__"):
            print(1)
        """
        expected = """
        class Test:
            pass

        callable(Test())
        callable("hi")
        
        assert callable(1)
        obj = Test()
        var = callable(obj)
        
        if callable(obj):
            print(1)
        """
        expected_diff_per_change = [
            """\
--- 
+++ 
@@ -2,7 +2,7 @@
 class Test:
     pass
 
-hasattr(Test(), "__call__")
+callable(Test())
 hasattr("hi", '__call__')
 
 assert hasattr(1, '__call__')
""",
            """\
--- 
+++ 
@@ -3,7 +3,7 @@
     pass
 
 hasattr(Test(), "__call__")
-hasattr("hi", '__call__')
+callable("hi")
 
 assert hasattr(1, '__call__')
 obj = Test()
""",
            """\
--- 
+++ 
@@ -5,7 +5,7 @@
 hasattr(Test(), "__call__")
 hasattr("hi", '__call__')
 
-assert hasattr(1, '__call__')
+assert callable(1)
 obj = Test()
 var = hasattr(obj, "__call__")
 
""",
            """\
--- 
+++ 
@@ -7,7 +7,7 @@
 
 assert hasattr(1, '__call__')
 obj = Test()
-var = hasattr(obj, "__call__")
+var = callable(obj)
 
 if hasattr(obj, "__call__"):
     print(1)
""",
            """\
--- 
+++ 
@@ -9,5 +9,5 @@
 obj = Test()
 var = hasattr(obj, "__call__")
 
-if hasattr(obj, "__call__"):
+if callable(obj):
     print(1)
""",
        ]

        self.run_and_assert(
            tmpdir, input_code, expected, expected_diff_per_change, num_changes=5
        )

    def test_other_hasattr(self, tmpdir):
        code = """
        from myscript import hasattr
        
        class Test:
            pass

        hasattr(Test(), "__call__")
        hasattr("hi", '__call__')
        """
        self.run_and_assert(tmpdir, code, code)

    def test_other_attr(self, tmpdir):
        code = """
        class Test:
            pass

        hasattr(Test(), "__repr__")
        hasattr("hi", '__repr__')
        """
        self.run_and_assert(tmpdir, code, code)

    def test_exclude_line(self, tmpdir):
        input_code = (
            expected
        ) = """
        class Test:
            pass
        obj = Test()
        hasattr(obj, "__call__")
        """
        lines_to_exclude = [5]
        self.run_and_assert(
            tmpdir,
            input_code,
            expected,
            lines_to_exclude=lines_to_exclude,
        )
