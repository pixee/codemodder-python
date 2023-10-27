Using mutable values for default arguments is not a safe practice.
Look at the following very simple example code:

```python
def foo(x, y=[]):
    y.append(x)
    print(y)
```

The function `foo` doesn't do anything very interesting; it just prints the result of `x` appended to `y`. Naively we might expect this to simply print an array containing only `x` every time `foo` is called, like this:

```python
>>> foo(1)
[1]
>>> foo(2)
[2]
```

But that's not what happens!

```python
>>> foo(1)
[1]
>>> foo(2)
[1, 2]
```

The value of `y` is preserved between calls! This might seem surprising, and it is. It's due to the way that scope works for function arguments in Python.

The result is that any default argument value will be preserved between function calls. This is problematic for *mutable* types, including things like `list`, `dict`, and `set`.

Relying on this behavior is unpredictable and generally considered to be unsafe. Most of us who write code like this were not anticipating the surprising behavior, so it's best to fix it.

Our codemod makes an update that looks like this:
```diff
- def foo(x, y=[]):
+ def foo(x, y=None):
+   y = [] if y is None else y
    y.append(x)
    print(y)
```

Using `None` is a much safer default. The new code checks if `None` is passed, and if so uses an empty `list` for the value of `y`. This will guarantee consistent and safe behavior between calls.
