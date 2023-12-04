For a `HttpReponse` in Django, if the `content_type` is not set, it default to `text/html`. If the JSON contains user supplied input without being sanitized first, a malicious user may supply HTTP code which leaves the application vulnerable to cross-site scripting (XSS). This transformation restricts the response type to `application/json` to avoid this vulnerability. Our changes look something like this:

```diff
from django.http import HttpResponse
import json

def foo(request):
    json_response = json.dumps({ "user_input": request.GET.get("input") })
-    return HttpResponse(json_response)
+    return HttpResponse(json_response, content_type="application/json")
```
