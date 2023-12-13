The default `mimetype` for `make_response` in Flask is `'text/html'`. This is true even when the response contains JSON data.
If the JSON contains (unsanitized) user-supplied input, a malicious user may supply HTML code which leaves the application vulnerable to cross-site scripting (XSS). 
This fix explicitly sets the response type to `application/json` when the response body is JSON data to avoid this vulnerability. Our changes look something like this:

```diff
from flask import make_response, Flask
import json

app = Flask(__name__)

@app.route("/test")
def foo(request):
    json_response = json.dumps({ "user_input": request.GET.get("input") })
-   return make_response(json_response)
+   return make_response(json_response, {'Content-Type':'application/json'})
```
