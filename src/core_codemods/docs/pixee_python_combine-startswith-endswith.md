Many developers are not necessarily aware that the `startswith` and `endswith` methods of `str` objects can accept a tuple of strings to match. This means that there is a lot of code that uses boolean expressions such as `x.startswith('foo') or x.startswith('bar')` instead of the simpler expression `x.startswith(('foo', 'bar'))`.

This codemod simplifies the boolean expressions where possible which leads to cleaner and more concise code.

The changes from this codemod look like this:

```diff
  x = 'foo'
- if x.startswith("foo") or x.startswith("bar"):
+ if x.startswith(("foo", "bar")):
     ...
```
