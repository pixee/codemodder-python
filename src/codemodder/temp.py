import sqlite3

name = input()
connection = sqlite3.connect("my_db.db")
cursor = connection.cursor()
cursor.execute("SELECT * from USERS WHERE name ='%s'" % name)


def foo():
    name = "user_%s_normal" % ("%s" % input())
    connection = sqlite3.connect("my_db.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * from USERS WHERE name ='%s'" % name)
