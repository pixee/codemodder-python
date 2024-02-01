The `is` and `is not` operators only evaluate to `True` when the expressions on each side have the same `id`. In other words, `a is b` is equivalent to `id(a) == id(b)`. With few exceptions, objects and literals have unique identities and thus shouldn't generally be compared by using the `is` or `is not` operators.

Our changes look something like this:

```diff
def foo(l):
-    return l is [1,2,3]
+    return l == [1,2,3]
```
