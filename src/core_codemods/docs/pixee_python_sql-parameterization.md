This codemod refactors SQL statements to be parameterized, rather than built by hand.

Without parameterization, developers must remember to escape string inputs using the rules for that column type and database. This usually results in bugs -- and sometimes vulnerability. Although it's not clear if this code is exploitable today, this change will make the code more robust in case the conditions which prevent exploitation today ever go away.

Our changes look something like this:

```diff
import sqlite3

name = input()
connection = sqlite3.connect("my_db.db")
cursor = connection.cursor()
- cursor.execute("SELECT * from USERS WHERE name ='" + name + "'")
+ cursor.execute("SELECT * from USERS WHERE name =?", (name, ))
```

If you have feedback on this codemod, [please let us know](mailto:feedback@pixee.ai)!

## F.A.Q.

### Why is this codemod marked as Merge With Cursory Review

Python has a wealth of database drivers that all use the same interface. Different drivers may require different string tokens used for parameterization, and Python's dynamic typing makes it quite hard, and sometimes impossible, to detect which driver is being used just by looking at the code.
