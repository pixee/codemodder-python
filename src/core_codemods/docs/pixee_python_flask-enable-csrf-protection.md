Flask views using `FlaskForm` have CSRF protection enabled by default. However other views may use AJAX to perform unsafe HTTP methods. FlaskWTF provides a way to enable CSRF protection globally for all views of a Flask app.
Our changes look something like this:

```diff
from flask import Flask
+from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
+csrf_app = CSRFProtect(app)
```
