import urllib3
import urllib3.connectionpool as pool
from urllib3 import HTTPConnectionPool as something

urllib3.HTTPConnectionPool("localhost", "80")
urllib3.connectionpool.HTTPConnectionPool("localhost", "80")
something("localhost", "80")
pool.HTTPConnectionPool("localhost", "80")
