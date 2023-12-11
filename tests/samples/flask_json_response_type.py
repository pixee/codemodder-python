from flask import make_response, Flask
import json

app = Flask(__name__)

@app.route("/test")
def foo(request):
    json_response = json.dumps({ "user_input": request.GET.get("input") })
    return make_response(json_response)
