import flask

response = flask.make_response()
var = "hello"
response.set_cookie("name", "value")

response2 = flask.Response()
var = "hello"
response2.set_cookie("name", "value")
