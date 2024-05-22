This codemod replaces all `tempfile.mktemp` calls with the more secure `tempfile.NamedTemporaryFile`

The Python [tempfile documentation](https://docs.python.org/3/library/tempfile.html#tempfile.mktemp) is explicit that `tempfile.mktemp` should be deprecated to avoid an unsafe and unexpected race condition. `tempfile.mktemp` does not handle the possibility that the returned file name could already be used by another process by the time your code opens the file. A more secure approach to create temporary files is to use `tempfile.NamedTemporaryFile` which will create the file for you and handle all security conditions. 

The changes from this codemod look like this:

```diff
  import tempfile
- filename = tempfile.mktemp()
+ with tempfile.NamedTemporaryFile(delete=False) as tf:
+     filename = tf.name
```

The change sets `delete=False` to closely follow your code's intention when calling `tempfile.mktemp`. However, you should use this as a starting point to determine when your temporary file should be deleted.
