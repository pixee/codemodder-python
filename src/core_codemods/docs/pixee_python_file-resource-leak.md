This codemod wraps assignments of `open` calls in a with statement. Without explicit closing, these resources will be "leaked" and won't be re-claimed until garbage collection. In situations where these resources are leaked rapidly (either through malicious repetitive action or unusually spiky usage), connection pool or file handle exhaustion will occur. These types of failures tend to be catastrophic, resulting in downtime and many times affect downstream applications.

Our changes look something like this:

```diff
import tempfile
path = tempfile.NamedTemporaryFile().name
-file = open(path, 'w', encoding='utf-8')
-file.write('Hello World')
+with open(path, 'w', encoding='utf-8') as file:
+   file.write('Hello World')
```
