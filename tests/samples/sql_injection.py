import sqlite3

connection = sqlite3.connect("my_db.db")

def foo(cursor: sqlite3.Cursor, name: str, phone:str):
    a = "SELECT * FROM Users"
    b = "WHERE name ='" + name
    c = "' AND phone = '" + phone + "'"
    cursor.execute(a + b + c)

foo(connection.cursor(), 'Jenny', '867-5309')
