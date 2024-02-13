This codemod updates places where two separate statements involving an assignment and conditional can be replaced with a single Assignment Expression (commonly known as the walrus operator).

Many developers use this operator in new code that they write but don't have the time to find and update every place in existing code. So we do it for you! We believe this leads to more concise and readable code.

The changes from this codemod look like this:

```diff
- x = foo()
- if x is not None:
+ if (x := foo()) is not None:
      print(x)
```
