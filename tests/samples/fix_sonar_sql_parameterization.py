import sqlite3

from flask import Flask, request

app = Flask(__name__)


@app.route("/example")
def f():
    user = request.args["user"]
    sql = """SELECT user FROM users WHERE user = \'%s\'"""

    conn = sqlite3.connect("example")
    conn.cursor().execute(sql % (user))
