The default `content_type` for `HttpResponse` in Django is `'text/html'`. This is true even when the response contains JSON data.
If the JSON contains (unsanitized) user-supplied input, a malicious user may supply HTML code which leaves the application vulnerable to cross-site scripting (XSS). 
This fix explicitly sets the response type to `application/json` when the response body is JSON data to avoid this vulnerability. Our changes look something like this:

```diff
from django.http import HttpResponse
import json

def foo(request):
    json_response = json.dumps({ "user_input": request.GET.get("input") })
-    return HttpResponse(json_response)
+    return HttpResponse(json_response, content_type="application/json")
```
