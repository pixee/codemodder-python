This codemod sets the most secure parameters when Flask applications call `set_cookie` on a response object. Without these parameters, your Flask
application cookies may be vulnerable to being intercepted and used to gain access to sensitive data.

The changes from this codemod look like this:

```diff
  from flask import Flask, session, make_response
  app = Flask(__name__)
  @app.route('/')
    def index():
      resp = make_response('Custom Cookie Set')
    - resp.set_cookie('custom_cookie', 'value')
    + resp.set_cookie('custom_cookie', 'value', secure=True, httponly=True, samesite='Lax')
      return resp
```
