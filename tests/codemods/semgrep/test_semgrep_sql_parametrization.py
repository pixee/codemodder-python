import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.semgrep.semgrep_sql_parameterization import (
    SemgrepSQLParameterization,
)


class TestSemgrepSQLParameterization(BaseSASTCodemodTest):
    codemod = SemgrepSQLParameterization
    tool = "semgrep"

    def test_name(self):
        assert self.codemod.name == "sql-parameterization"

    def test_import(self, tmpdir):
        input_code = '''\
        import sqlite3
        
        from flask import Flask, request
        
        app = Flask(__name__)
        
        
        @app.route("/example")
        def f():
            user = request.args["user"]
            sql = """SELECT user FROM users WHERE user = \'%s\'"""
        
            conn = sqlite3.connect("example")
            conn.cursor().execute(sql % (user))
        '''
        expexted_output = '''\
        import sqlite3
        
        from flask import Flask, request
        
        app = Flask(__name__)
        
        
        @app.route("/example")
        def f():
            user = request.args["user"]
            sql = """SELECT user FROM users WHERE user = ?"""
        
            conn = sqlite3.connect("example")
            conn.cursor().execute(sql, ((user), ))
        '''
        expected_diff_per_change = [
            '''\
--- 
+++ 
@@ -8,7 +8,7 @@
 @app.route("/example")
 def f():
     user = request.args["user"]
-    sql = """SELECT user FROM users WHERE user = '%s'"""
+    sql = """SELECT user FROM users WHERE user = ?"""
 
     conn = sqlite3.connect("example")
-    conn.cursor().execute(sql % (user))
+    conn.cursor().execute(sql, ((user), ))
''',
            '''\
--- 
+++ 
@@ -8,7 +8,7 @@
 @app.route("/example")
 def f():
     user = request.args["user"]
-    sql = """SELECT user FROM users WHERE user = '%s'"""
+    sql = """SELECT user FROM users WHERE user = ?"""
 
     conn = sqlite3.connect("example")
-    conn.cursor().execute(sql % (user))
+    conn.cursor().execute(sql, ((user), ))
''',
        ]

        results = {
            "runs": [
                {
                    "tool": {"driver": {"name": "Semgrep OSS"}},
                    "results": [
                        {
                            "guid": "2273caac-50fa-409d-97e8-a39219eb9afe",
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 40,
                                            "endLine": 14,
                                            "snippet": {
                                                "text": '    user = request.args["user"]\n    sql = """SELECT user FROM users WHERE user = \\\'%s\\\'"""\n\n    conn = sqlite3.connect("example")\n    conn.cursor().execute(sql % (user))'
                                            },
                                            "startColumn": 5,
                                            "startLine": 10,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "User-controlled data from a request is passed to 'execute()'. This could lead to a SQL injection and therefore protected information could be leaked. Instead, use django's QuerySets, which are built with query parameterization and therefore not vulnerable to sql injection. For example, you could use `Entry.objects.filter(date=2006)`."
                            },
                            "properties": {},
                            "ruleId": "python.django.security.injection.sql.sql-injection-using-db-cursor-execute.sql-injection-db-cursor-execute",
                        },
                        {
                            "guid": "8e8fed36-7e72-4b1f-ad49-2e1a50587595",
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 40,
                                            "endLine": 14,
                                            "snippet": {
                                                "text": "    conn.cursor().execute(sql % (user))"
                                            },
                                            "startColumn": 5,
                                            "startLine": 14,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected possible formatted SQL query. Use parameterized queries instead."
                            },
                            "properties": {},
                            "ruleId": "python.lang.security.audit.formatted-sql-query.formatted-sql-query",
                        },
                        {
                            "guid": "300df87d-e713-4cd4-a245-d64f25be03de",
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 40,
                                            "endLine": 14,
                                            "snippet": {
                                                "text": "    conn.cursor().execute(sql % (user))"
                                            },
                                            "startColumn": 5,
                                            "startLine": 14,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Avoiding SQL string concatenation: untrusted input concatenated with raw SQL query can result in SQL Injection. In order to execute raw query safely, prepared statement should be used. SQLAlchemy provides TextualSQL to easily used prepared statement with named parameters. For complex SQL composition, use SQL Expression Language or Schema Definition Language. In most cases, SQLAlchemy ORM will be a better option."
                            },
                            "properties": {},
                            "ruleId": "python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query",
                        },
                        {
                            "guid": "24695222-6db9-4e12-8555-c5e74eb7fe0f",
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 39,
                                            "endLine": 14,
                                            "snippet": {
                                                "text": "    conn.cursor().execute(sql % (user))"
                                            },
                                            "startColumn": 27,
                                            "startLine": 14,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction could accidentally result in a SQL injection. An attacker could use a SQL injection to steal or modify contents of the database. Instead, use a parameterized query which is available by default in most database engines. Alternatively, consider using the Django object-relational mappers (ORM) instead of raw SQL queries."
                            },
                            "properties": {},
                            "ruleId": "python.django.security.injection.tainted-sql-string.tainted-sql-string",
                        },
                        {
                            "guid": "c8355088-665d-4fe1-8790-725964ba0769",
                            "fingerprints": {"matchBasedId/v1": "123"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "code.py",
                                            "uriBaseId": "%SRCROOT%",
                                        },
                                        "region": {
                                            "endColumn": 39,
                                            "endLine": 14,
                                            "snippet": {
                                                "text": "    conn.cursor().execute(sql % (user))"
                                            },
                                            "startColumn": 27,
                                            "startLine": 14,
                                        },
                                    }
                                }
                            ],
                            "message": {
                                "text": "Detected user input used to manually construct a SQL string. This is usually bad practice because manual construction could accidentally result in a SQL injection. An attacker could use a SQL injection to steal or modify contents of the database. Instead, use a parameterized query which is available by default in most database engines. Alternatively, consider using an object-relational mapper (ORM) such as SQLAlchemy which will protect your queries."
                            },
                            "properties": {},
                            "ruleId": "python.flask.security.injection.tainted-sql-string.tainted-sql-string",
                        },
                    ],
                }
            ]
        }
        self.run_and_assert(
            tmpdir,
            input_code,
            expexted_output,
            expected_diff_per_change,
            results=json.dumps(results),
            num_changes=2,
        )
