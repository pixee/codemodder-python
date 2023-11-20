Flask applications can configure sessions behavior at the application level. 
This codemod looks for Flask application configuration that set `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, or `SESSION_COOKIE_SAMESITE` to an insecure value and changes it to a secure one.

The changes from this codemod look like this:

```diff
  from flask import Flask
  app = Flask(__name__)
- app.config['SESSION_COOKIE_HTTPONLY'] = False
- app.config.update(SESSION_COOKIE_SECURE=False)
+ app.config['SESSION_COOKIE_HTTPONLY'] = True
+ app.config.update(SESSION_COOKIE_SECURE=True)
```
