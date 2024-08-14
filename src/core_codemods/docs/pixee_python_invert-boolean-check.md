This codemod flips boolean `not` comparisons to their more readable equivalent comparisons.

The changes from this codemod look like this:

```diff
- assert not user_input == "yes"
- z = not m <= n
+ assert user_input != "yes"
+ z = m > n
```
