When defining a Python dataclass it is not safe to use mutable datatypes (such as `list`, `dict`, or `set`) as defaults for the attributes. This is because the defined attribute will be shared by all instances of the dataclass type. Using such a mutable default will ultimately result in a `ValueError` at runtime. This codemod updates attributes of `dataclasses.dataclass` with mutable defaults to use `dataclasses.field` instead. The [dataclass documentation](https://docs.python.org/3/library/dataclasses.html#mutable-default-values) providesmore details about why using `field(default_factory=...)` is the recommended pattern.

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
