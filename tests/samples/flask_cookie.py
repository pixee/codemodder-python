from flask import Flask, session, make_response

app = Flask(__name__)

@app.route('/')
def index():
    resp = make_response('Custom Cookie Set')
    resp.set_cookie('custom_cookie', 'value')
    return resp
