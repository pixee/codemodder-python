This codemod converts "eager" logging into "lazy" logging, which is preferred for performance efficiency and resource optimization.
Lazy logging defers the actual construction and formatting of log messages until it's confirmed that the message will be logged based on the current log level, thereby avoiding unnecessary computation for messages that will not be logged. 

Our changes look something like this:

```diff
import logging
e = "Some error"
- logging.error("Error occurred: %s" % e)
- logging.error("Error occurred: " + e)
+ logging.error("Error occurred: %s", e)
+ logging.error("Error occurred: %s", e)
```
