This codemod refactors SQL statements to be parameterized, rather than built by hand.

Without parameterization, developers must remember to escape string inputs using the rules for that column type and database. This usually results in bugs -- and sometimes vulnerabilities. Although we can't tell for sure if your code is actually exploitable, this change will make the code more robust in case the conditions which prevent exploitation today ever go away.

Our changes look something like this:

```diff
import sqlite3

name = input()
connection = sqlite3.connect("my_db.db")
cursor = connection.cursor()
- cursor.execute("SELECT * from USERS WHERE name ='" + name + "'")
+ cursor.execute("SELECT * from USERS WHERE name =?", (name, ))
```
