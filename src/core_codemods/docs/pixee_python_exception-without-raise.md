This codemod fixes cases where an exception is referenced by itself in a statement without being raised. This most likely indicates a bug: you probably meant to actually raise the exception. 

Our changes look something like this:
```diff
try:
-   ValueError
+   raise ValueError
except:
    pass
```
