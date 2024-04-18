The default value for the `abs_tol` argument to a `math.isclose` call is `0`. Using this default when comparing a value against `0`, such as in `math.isclose(a, 0)` is equivalent to a strict equality check to `0`, which is not the intended use of the `math.isclose` function.

This codemod adds `abs_tol=1e-09` to any call to `math.isclose` with one of of the first arguments evaluating to `0` if `abs_tol` is not already specified. `1e-09` is a starting point for you to consider depending on your calculation needs.

Our changes look like the following:
```diff
+import math
+
 def foo(a):
-    return math.isclose(a, 0)
+    return math.isclose(a, 0, abs_tol=1e-09)
```
