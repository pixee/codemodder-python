The context manager object `pytest.raises(<exception>)` will assert if the code contained within its scope will raise an exception of type `<exception>`. The documentation points that the exception must be raised in the last line of its scope and any line afterwards won't be executed. 
Including asserts at the end of the scope is a common error. This codemod addresses that by moving them out of the scope.
Our changes look something like this:

```diff
import pytest

def test_foo():
    with pytest.raises(ZeroDivisionError):
        error = 1/0
-       assert 1
-       assert 2
+   assert 1
+   assert 2
```
