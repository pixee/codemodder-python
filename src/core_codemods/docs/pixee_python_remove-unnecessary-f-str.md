This codemod converts any f-strings without interpolated variables into regular strings.
In these cases the use of f-string is not necessary; a simple string literal is sufficient. 

While in some (extreme) cases we might expect a very modest performance
improvement, in general this is a fix that improves the overall cleanliness and
quality of your code.

```diff
- var = f"hello"
+ var = "hello"
  ...
```
