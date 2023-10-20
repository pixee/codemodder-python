import sqlite3

connection = sqlite3.connect("tests/samples/my_db.db")


def foo(cursor: sqlite3.Cursor, name: str, phone: str):
    a = "SELECT * FROM Users"
    b = " WHERE name ='" + name
    c = "' AND phone = '" + phone + "'"
    r = cursor.execute(a + b + c)
    print(r.fetchone())


foo(connection.cursor(), "Jenny", "867-5309")
