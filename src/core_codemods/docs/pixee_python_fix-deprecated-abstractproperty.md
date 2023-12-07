The `@abstractproperty` decorator from `abc` has been [deprecated](https://docs.python.org/3/library/abc.html#abc.abstractproperty) since Python 3.3. This is because it's possible to use `@property` in combination with `@abstractmethod`. 

Our changes look like the following:
```diff
 import abc

 class Foo:
-   @abc.abstractproperty
+   @property
+   @abc.abstractmethod
    def bar():
        ...
```
