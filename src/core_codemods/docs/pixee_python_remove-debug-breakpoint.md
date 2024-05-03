This codemod removes any calls to `breakpoint()` or `pdb.set_trace()` which are generally only used for interactive debugging and should not be deployed in production code.

In most cases if these calls are included in committed code, they were left there by mistake and indicate a potential problem.

Our changes look something like this:

```diff
 print("hello")
- breakpoint()
 print("world")
```
