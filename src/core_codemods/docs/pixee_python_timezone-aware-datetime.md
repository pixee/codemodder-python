Some `datetime` object calls use the machine's local timezone instead of a reasonable default like UTC. This may be okay in some cases, but it can lead to bugs.  Misinterpretation of dates have been the culprit for serious issues in banking, satellite communications, and other industries.

The `datetime` [documentation](https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow) explicitly encourages using timezone aware objects to prevent bugs.

Our changes look like the following:
```diff
 import datetime
 import time

- datetime.datetime(2021, 12, 25, 15, 30, 0)
- datetime.datetime.now()
- datetime.datetime.fromtimestamp(time.time())
+ datetime.datetime(2021, 12, 25, 15, 30, 0, tzinfo=datetime.timezone.utc)
+ datetime.datetime.now(tz=datetime.timezone.utc)
+ datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc)
```
