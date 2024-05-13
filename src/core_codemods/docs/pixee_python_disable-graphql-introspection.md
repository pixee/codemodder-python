Introspection allows a client to query the schema of a GraphQL API. Allowing introspection in production code may allow a malicious user to gather information about data types and operations for a potential attack.

Introspection is often enabled by default in GraphQL without authentication. This codemod disables introspection altogether at the view level by introducing a validation rule. The required rules may be dependent on the framework that you are using. Please check your framework documentation for specific rules for disabling introspection.

Our changes look something like this:
```diff
from graphql_server.flask import GraphQLView
from flask import Flask
from graphql import (
    GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)
+from graphql.validation import NoSchemaIntrospectionCustomRule

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
    view_func=GraphQLView.as_view(  # Noncompliant
        name="api",
        schema=schema,
+       validation_rules = [NoSchemaIntrospectionCustomRule]
    ),
)
```
