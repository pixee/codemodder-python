This codemod replaces all `tempfile.mktemp` calls to the more secure `tempfile.mkstemp`.

The Python [tempfile documentation](https://docs.python.org/3/library/tempfile.html#tempfile.mktemp) is explicit
that `tempfile.mktemp` should be deprecated to avoid an unsafe and unexpected race condition.
The changes from this codemod look like this:


```diff
  import tempfile
- tempfile.mktemp(...)
+ tempfile.mkstemp(...)
```
