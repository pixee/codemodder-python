import flask

response = flask.make_response()
var = "hello"
response.set_cookie("name", "value", secure=True, httponly=True, samesite="Lax")

response2 = flask.Response()
var = "hello"
response2.set_cookie("name", "value", secure=True, httponly=True, samesite="Lax")
