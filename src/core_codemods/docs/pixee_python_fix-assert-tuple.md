An assertion on a non-empty tuple will always evaluate to `True` so it's likely to be written unintentionally. This codemod will write one assert statement for each item in the tuple.



The changes from this codemod look like this:

```diff
- assert (1 == 1, 2 == 2)
+ assert 1 == 1
+ assert 2 == 2
```
