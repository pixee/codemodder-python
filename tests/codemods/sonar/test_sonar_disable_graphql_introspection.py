import json

from codemodder.codemods.test import BaseSASTCodemodTest
from core_codemods.sonar.sonar_disable_graphql_introspection import (
    SonarDisableGraphQLIntrospection,
)


class TestSonarDisableGraphQLIntrospection(BaseSASTCodemodTest):
    codemod = SonarDisableGraphQLIntrospection
    tool = "sonar"

    def test_name(self):
        assert self.codemod.name == "disable-graphql-introspection"

    def test_simple(self, tmpdir):
        input_code = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema

        app = Flask(__name__)

        app.add_url_rule("/api",
            view_func=GraphQLView.as_view(
                name="api",
                schema=schema,
            ),
        )
        """
        expected = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphql.validation import NoSchemaIntrospectionCustomRule

        app = Flask(__name__)

        app.add_url_rule("/api",
            view_func=GraphQLView.as_view(
                name="api",
                schema=schema,
            validation_rules = [NoSchemaIntrospectionCustomRule,]),
        )
        """
        issues = {
            "issues": [
                {
                    "rule": "python:S6786",
                    "status": "OPEN",
                    "component": "code.py",
                    "textRange": {
                        "startLine": 9,
                        "endLine": 9,
                        "startOffset": 14,
                        "endOffset": 33,
                    },
                }
            ]
        }
        self.run_and_assert(tmpdir, input_code, expected, results=json.dumps(issues))
