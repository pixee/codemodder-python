Many developers are not necessarily aware that the `isinstance` and `issubclass` builtin methods can accept a tuple of classes to match. This means that there is a lot of code that uses boolean expressions such as `isinstance(x, str) or isinstance(x, bytes)` instead of the simpler expression `isinstance(x, (str, bytes))`.

This codemod simplifies the boolean expressions where possible which leads to cleaner and more concise code.

The changes from this codemod look like this:

```diff
  x = 'foo'
- if isinstance(x, str) or isinstance(x, bytes):
+ if isinstance(x, (str, bytes)):
     ...
```
