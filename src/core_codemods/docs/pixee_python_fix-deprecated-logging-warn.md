The `warn` method from `logging` has been [deprecated](https://docs.python.org/3/library/logging.html#logging.Logger.warning) since Python 3.3. 

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
