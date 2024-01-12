Cross-site request forgery (CSRF) is an attack where a user is tricked by a malicious agent to submit a unintended request (e.g login requests). A common way to mitigate this issue is to embed an additional token into requests to identify requests from unauthorized locations.

Flask views using `FlaskForm` have CSRF protection enabled by default. However other views may use AJAX to perform unsafe HTTP methods. FlaskWTF provides a way to enable CSRF protection globally for all views of a Flask app.

The changes in this codemod may require manual additions to maintain proper functionality. You need to setup either a flask `SECRET_KEY` or a `WTF_CSRF_SECRET_KEY` in you app configuration and adjust any views with HTML forms and javascript requests to include the CSRF token. See the [FlaskWTF docs](https://flask-wtf.readthedocs.io/en/1.2.x/csrf/) for examples on how to do it.

Our changes look something like this:

```diff
from flask import Flask
+from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
+csrf_app = CSRFProtect(app)
```
