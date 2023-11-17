from test_sources import untrusted_data
import requests

url = untrusted_data()
requests.get(url)
var = "hello"
