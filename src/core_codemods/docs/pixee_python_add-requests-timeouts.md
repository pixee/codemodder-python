Many developers will be surprised to learn that `requests` library calls do not include timeouts by default. This means that an attempted request could hang indefinitely if no connection is established or if no data is received from the server. 

The [requests documentation](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts) suggests that most calls should explicitly include a `timeout` parameter. This codemod adds a default timeout value in order to set an upper bound on connection times and ensure that requests connect or fail in a timely manner. This value also ensures the connection will timeout if the server does not respond with data within a reasonable amount of time. 

While timeout values will be application dependent, we believe that this codemod adds a reasonable default that serves as an appropriate ceiling for most situations. 

Our changes look like the following:
```diff
 import requests
 
- requests.get("http://example.com")
+ requests.get("http://example.com", timeout=60)
```
