from flask import Flask, send_file

app = Flask(__name__)

@app.route("/uploads/<path:name>")
def download_file(name):
    return send_file(f'path/to/{name}.txt')
