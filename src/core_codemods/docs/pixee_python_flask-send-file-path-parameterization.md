The `send_file` function from Flask is susceptible to a path injection attack if its input is not proper validated. 
In a path injection attack, the malicious agent can craft a path containing special paths like `./` or `../` to resolve an unintended file. This allows the agent to overwrite, delete or read arbitrary files.
Flask offers a native solution with the `flask.send_from_directory` function that validates the given path.

Our changes look something like this:

```diff
-from flask import Flask, send_file
+from flask import Flask
+import flask
+from pathlib import Path

app = Flask(__name__)

@app.route("/uploads/<path:name>")
def download_file(name):
-    return send_file(f'path/to/{name}.txt')
+    return flask.send_from_directory((p := Path(f'path/to/{name}.txt')).parent, p.name)
```
