from flask import Flask
from graphql_server.flask import GraphQLView
from graphql.validation import NoSchemaIntrospectionCustomRule

GraphQLView.as_view(
    "api",
    validation_rules=[
        NoSchemaIntrospectionCustomRule,
    ],
)


app = Flask(__name__)
app.add_url_rule(
    "/api",
    view_func=GraphQLView.as_view(
        name="api",
        validation_rules=[
            NoSchemaIntrospectionCustomRule,
        ],
    ),
)
