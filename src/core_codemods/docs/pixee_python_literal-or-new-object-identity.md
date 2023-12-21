The `is` and `is not` operator will only return `True` when the expression have the same `id`. In other words, `a is b` is equivalent to `id(a) == id(b)`. New objects and literals have their own identities and thus shouldn't be compared with using the `is` or `is not` operators.

Our changes look something like this:

```diff
def foo(l):
-    return l is [1,2,3]
+    return l == [1,2,3]
```
