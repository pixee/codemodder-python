This codemod fixes cases where `hasattr` is used to check if an object is a callable. You likely want to use `callable` instead. This is because using `hasattr` will return different results in some cases, such as when the class implements a `__getattr__` method. 

Our changes look something like this:
```diff
 class Test:
     pass

 obj = Test()
- hasattr(obj, "__call__")
+ callable(obj)
```
