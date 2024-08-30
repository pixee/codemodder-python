Some `datetime` object calls use the machine's local timezone instead of a reasonable default like UTC. This may be okay in some cases, but it can lead to bugs.  Misinterpretation of dates have been the culprit for serious issues in banking, satellite communications, and other industries.

The `datetime` [documentation](https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow) explicitly encourages using timezone aware objects to prevent bugs.

Our changes look like the following:
```diff
 from datetime import datetime
 import time

- datetime.utcnow()
- datetime.utcfromtimestamp(time.time())
+ datetime.now(tz=timezone.utc)
+ datetime.fromtimestamp(time.time(), tz=timezone.utc)
```
