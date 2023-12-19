Many older codebases have `__future__` imports for forwards compatibility with features. As of this writing, all but one of those features is now stable in all currently supported versions of Python and so the imports are no longer needed. While such imports are harmless, they are also unnecessary and in most cases you probably just forgot to remove them. 

This codemod removes all such `__future__` imports, preserving only those that are still necessary for forwards compatibility. 

Our changes look like the following:
```diff
 import os
-from __future__ import print_function

 print("HELLO")
```
