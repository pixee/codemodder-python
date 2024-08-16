import datetime
import time
from zoneinfo import ZoneInfo

datetime.datetime(2021, 12, 25, 15, 30, 0)

datetime.datetime.now()

datetime.datetime.fromtimestamp(time.time())

# should match
datetime.datetime.utcnow()
timestamp = 1571595618.0
datetime.datetime.utcfromtimestamp(timestamp)

datetime.datetime.today()
datetime.date.today()


datetime.date.fromtimestamp(time.time())
eastern = ZoneInfo("America/New_York")
datetime.date.fromtimestamp(time.time(), eastern)
datetime.date.fromtimestamp(time.time(), tz=eastern)

datetime.datetime.utcfromtimestamp(time.time(), eastern)
datetime.datetime.utcfromtimestamp(time.time(), tz=eastern)
