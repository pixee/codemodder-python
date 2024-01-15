Empty sequences in a boolean comparison expression are considered falsy so you can use implicit boolean comparisons instead of
comparing against empty sequences directly

Our changes look like the following:
```diff
 x = [1]

- if x != []:
+ if x:
    pass 
```
