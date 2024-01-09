The `warn` method from `logging` has been [deprecated](https://docs.python.org/3/library/logging.html#logging.Logger.warning) in favor of `warning` since Python 3.3. Since the old method `warn` has been retained for a long time, there are a lot of developers that are unaware of this change and consequently a lot of code using the older method.

Our changes look like the following:
```diff
 import logging

- logging.warn("hello")
+ logging.warning("hello")
 ...
 log = logging.getLogger("my logger")
- log.warn("hello")
+ log.warning("hello") 
```
