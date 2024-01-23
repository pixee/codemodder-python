An assertion on a non-empty tuple will always evaluate to `True`. This means that `assert` statements involving non-empty tuple literals are likely unintentional and should be rewritten. This codemod rewrites the original `assert` statement by creating a new `assert` for each item in the original tuple.

The changes from this codemod look like this:

```diff
- assert (1 == 1, 2 == 2)
+ assert 1 == 1
+ assert 2 == 2
```
