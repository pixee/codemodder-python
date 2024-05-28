from flask import app, request
from lxml import etree
import lxml.etree


@app.route("/authenticate")
def authenticate():
    username = request.args["username"]
    password = request.args["password"]
    expression = "./users/user[@name='" + username + "' and @pass='" + password + "']"
    tree = etree.parse("resources/users.xml", parser=lxml.etree.XMLParser(resolve_entities=False))

    if tree.find(expression) is None:
        return "Invalid credentials", 401
    else:
        return "Success", 200
