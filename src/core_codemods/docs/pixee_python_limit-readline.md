This codemod hardens all [`readline()`](https://docs.python.org/3/library/io.html#io.IOBase.readline) calls from file objects returned from an `open()` call, `StringIO` and `BytesIO` against denial of service attacks. A stream influenced by an attacker could keep providing bytes until the system runs out of memory, causing a crash.

Fixing it is straightforward by providing adding a size argument to any `readline()` calls.
The changes from this codemod look like this:

```diff
  file = open('some_file.txt')
- file.readline()
+ file.readline(5_000_000)
```
