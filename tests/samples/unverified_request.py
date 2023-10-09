import requests

requests.get("https://www.google.com", verify=False)
requests.post("https://some-api/", json={"id": 1234, "price": 18}, verify=False)
var = "hello"
