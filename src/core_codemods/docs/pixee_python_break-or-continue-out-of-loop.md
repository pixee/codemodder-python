Any `break` or `continue` statements that are not inside a `for` or `while` loop will result in a `SyntaxError`. This codemod will remove them.

Our changes look something like this:

```diff
def f():
     print('not in a loop')
-    break
```
