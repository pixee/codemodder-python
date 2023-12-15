import requests

requests.get("https://example.com")
requests.get("https://example.com", timeout=1)
requests.get("https://example.com", timeout=(1, 10), verify=False)
requests.post("https://example.com", verify=False)
