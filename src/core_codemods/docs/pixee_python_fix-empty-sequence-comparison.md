Empty sequences in Python always evaluate to `False`. This means that comparison expressions that use empty sequences can sometimes be simplified. In these cases no explicit comparison is required: instead we can rely on the [truth value](https://docs.python.org/3/library/stdtypes.html#truth-value-testing) of the object under comparison. This is sometimes referred to as "implicit" comparison. Using implicit boolean comparison expressions is considered best practice and can lead to better code.

Our changes look like the following:
```diff
 x = [1]

- if x != []:
+ if x:
    pass 
```
