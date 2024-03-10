This codemod will fix instances of `dataclasses.dataclass` that define default lists, sets, or dicts which raise a runtime `ValueError`. The [dataclass documentation](https://docs.python.org/3/library/dataclasses.html#mutable-default-values) provides a clear explanation of why this code is disallowed and explains how to use `field(default_factory=...)` instead.

Our changes look something like this:

```diff
-from dataclasses import dataclass
+from dataclasses import field, dataclass

 @dataclass
 class Person:
     name: str = ""
-    phones: list = []
-    friends: dict = {}
-    family: set = set()
+    phones: list = field(default_factory=list)
+    friends: dict = field(default_factory=dict)
+    family: set = field(default_factory=set)
```
