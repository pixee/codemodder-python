This codemod removes any calls to `breakpoint()` or `pdb.set_trace()` which should only be used for active debugging and not in production code.

```diff
 print("hello")
- breakpoint()
 print("world")
```
