from flask import Flask, request
from security import safe_requests

app = Flask(__name__)


@app.route("/example")
def example():
    url = request.args["url"]
    safe_requests.get(url, timeout=60)
