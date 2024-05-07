from graphql_server.flask import GraphQLView
from flask import Flask
from graphql import (
    GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)

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
    ),
)
