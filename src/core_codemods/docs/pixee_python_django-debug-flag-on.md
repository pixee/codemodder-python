This codemod will flip Django's `DEBUG` flag to `False` if it's `True` on the `settings.py` file within Django's default directory structure.

Having the debug flag on may result in sensitive information exposure. When an exception occurs while the `DEBUG` flag in on, it will dump metadata of your environment, including the settings module. The attacker can purposefully request a non-existing url to trigger an exception and gather information about your system.

```diff
- DEBUG = True
+ DEBUG = False
```
