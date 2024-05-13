from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.disable_graphql_introspection import (
    DisableGraphQLIntrospectionTransform,
)
from core_codemods.sonar.sonar_disable_graphql_introspection import (
    SonarDisableGraphQLIntrospection,
)


class TestSonarDisableGraphQLIntrospection(SonarIntegrationTest):
    codemod = SonarDisableGraphQLIntrospection
    code_path = "tests/samples/disable_graphql_introspection.py"
    expected_new_code = """\
    from graphql_server.flask import GraphQLView
    from flask import Flask
    from graphql import (
        GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)
    from graphql.validation import NoSchemaIntrospectionCustomRule

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='RootQueryType',
            fields={
                'hello': GraphQLField(
                    GraphQLString,
                    resolve=lambda obj, info: 'world')
            }))

    app = Flask(__name__)

    app.add_url_rule("/api",
        view_func=GraphQLView.as_view(
            name="api",
            schema=schema,
        validation_rules = [NoSchemaIntrospectionCustomRule,]),
    )
    """

    # fmt: off
    expected_diff = (
        """--- \n"""
        """+++ \n"""
        """@@ -2,6 +2,7 @@\n"""
        """ from flask import Flask\n"""
        """ from graphql import (\n"""
        """     GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)\n"""
        """+from graphql.validation import NoSchemaIntrospectionCustomRule\n"""
        """ \n"""
        """ schema = GraphQLSchema(\n"""
        """     query=GraphQLObjectType(\n"""
        """@@ -18,5 +19,5 @@\n"""
        """     view_func=GraphQLView.as_view(\n"""
        """         name="api",\n"""
        """         schema=schema,\n"""
        """-    ),\n"""
        """+    validation_rules = [NoSchemaIntrospectionCustomRule,]),\n"""
        """ )\n"""
    )
    # fmt: on

    expected_line_change = "18"
    change_description = DisableGraphQLIntrospectionTransform.change_description
    num_changed_files = 1
