This codemod converts any f-strings without interpolation to regular strings.

```diff
- var = f"hello"
+ var = "hello"
  ...
```
