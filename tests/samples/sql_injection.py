import sqlite3

connection = sqlite3.connect(":memory:")
connection.cursor().execute("CREATE TABLE Users (name, phone)")
connection.cursor().execute("INSERT INTO Users VALUES ('Jenny','867-5309')")


def foo(cursor: sqlite3.Cursor, name: str, phone: str):
    a = "SELECT * FROM Users"
    b = " WHERE name ='" + name
    c = "' AND phone = '" + phone + "'"
    r = cursor.execute(a + b + c)
    print(r.fetchone())


foo(connection.cursor(), "Jenny", "867-5309")
