Using the `global` keyword is necessary only when you intend to modify a module-level (aka global) variable within a non-global scope, such as within a class or function. It is unnecessary to call `global` at the module-level.

Our changes look something like this:

```diff
 price = 25
 print("hello")
- global price
 price = 30
```
