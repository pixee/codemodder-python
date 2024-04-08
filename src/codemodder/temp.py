import sqlite3

name = input()
connection = sqlite3.connect("my_db.db")
cursor = connection.cursor()
cursor.execute("SELECT * from USERS WHERE name =?", (name,))
