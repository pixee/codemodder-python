This codemod fixes cases of implicit string concatenation inside lists, sets, or tuples. This is most likely a mistake: you probably meant include a comma in between the concatenated strings. 

Our changes look something like this:
```diff
bad = [
-    "ab"
+    "ab",
     "cd",
     "ef",
-    "gh"
+    "gh",
     "ij",
]
```
