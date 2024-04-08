In most programming languages, floating point arithmetic is imprecise due to the way floating point numbers are stored as binary representations. Moreover, the result of calculations with floats can vary based on when rounding happens. Using equality or inequality to compare floats or their operations will almost always be imprecise and lead to bugs.

For these reasons, this codemod changes any operations involving equality or inequality with floats to the recommended `math.isclose` function. This codemod uses the default parameter values `rel_tol=1e-09` and  `abs_tol=0.0` but makes them explicit as a starting point for you to consider depending on your calculation needs.

Our changes look like the following:
```diff
+import math
+
 def foo(a, b):
-    return a == b - 0.1
+    return math.isclose(a, b - 0.1, rel_tol=1e-09, abs_tol=0.0)
```
