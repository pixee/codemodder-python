import sqlite3


def f(user):
    sql = """SELECT user FROM users WHERE user = ?"""

    conn = sqlite3.connect("example")
    conn.cursor().execute(sql, ((user),))  # Noncompliant


def g(user):
    sql = "SELECT user FROM users WHERE user = '" + user + "'"

    conn = sqlite3.connect("example")
    conn.cursor().execute(sql)  # Noncompliant
