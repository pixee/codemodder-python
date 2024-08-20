from flask import Flask
from graphql_server.flask import GraphQLView

GraphQLView.as_view("api")


app = Flask(__name__)
app.add_url_rule(
    "/api",
    view_func=GraphQLView.as_view(
        name="api",
    ),
)
