import requests
from flask import Flask, request

app = Flask(__name__)


@app.route("/example")
def example():
    url = request.args["url"]
    requests.get(url)
