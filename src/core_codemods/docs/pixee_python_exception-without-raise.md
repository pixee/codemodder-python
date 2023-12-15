An statement with an exception without raising it is most likely an error. Our changes look something like this:

```diff
try:
-   ValueError
+   raise ValueError
except:
    pass
```
