import pytest

from codemodder.codemods.test import BaseCodemodTest
from core_codemods.disable_graphql_introspection import DisableGraphQLIntrospection


class TestDisableGraphQLIntrospection(BaseCodemodTest):
    codemod = DisableGraphQLIntrospection

    def test_name(self):
        assert self.codemod.name == "disable-graphql-introspection"

    def test_simple_flask(self, tmpdir):
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
        self.run_and_assert(tmpdir, input_code, expected)

    @pytest.mark.parametrize(
        "module",
        [
            "graphql_server.flask",
            "graphql_server.sanic",
            "graphql_server.aiohttp",
            "graphql_server.webob",
        ],
    )
    def test_simple_constructor(self, tmpdir, module):
        input_code = f"""
        from {module} import GraphQLView
        from flask import Flask
        from .schemas import schema

        GraphQLView(
            name="api",
            schema=schema,
        )
        """
        expected = f"""
        from {module} import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphql.validation import NoSchemaIntrospectionCustomRule

        GraphQLView(
            name="api",
            schema=schema,
        validation_rules = [NoSchemaIntrospectionCustomRule,])
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_add_indirect(self, tmpdir):
        input_code = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema

        validation_rules = []
        GraphQLView(
            name="api",
            schema=schema,
            validation_rules = validation_rules,
        )
        """
        expected = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphql.validation import NoSchemaIntrospectionCustomRule

        validation_rules = [NoSchemaIntrospectionCustomRule]
        GraphQLView(
            name="api",
            schema=schema,
            validation_rules = validation_rules,
        )
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_add_list_double_indirect(self, tmpdir):
        input_code = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema

        validation_rules = []
        GraphQLView(
            name="api",
            schema=schema,
            validation_rules = [*validation_rules],
        )
        """
        expected = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphql.validation import NoSchemaIntrospectionCustomRule

        validation_rules = []
        GraphQLView(
            name="api",
            schema=schema,
            validation_rules = [*validation_rules, NoSchemaIntrospectionCustomRule],
        )
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_add_dict_indirect(self, tmpdir):
        input_code = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema

        validation_rules = []
        kwargs = {'validation_rules' : validation_rules}
        GraphQLView(
            name="api",
            schema=schema,
            **kwargs,
        )
        """
        expected = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphql.validation import NoSchemaIntrospectionCustomRule

        validation_rules = [NoSchemaIntrospectionCustomRule]
        kwargs = {'validation_rules' : validation_rules}
        GraphQLView(
            name="api",
            schema=schema,
            **kwargs,
        )
        """
        self.run_and_assert(tmpdir, input_code, expected)

    def test_has_validation_rule(self, tmpdir):
        input_code = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphql.validation import NoSchemaIntrospectionCustomRule

        GraphQLView(
            name="api",
            schema=schema,
            validation_rules = [NoSchemaIntrospectionCustomRule],
        )
        """
        self.run_and_assert(tmpdir, input_code, input_code)

    def test_has_graphene_validation_rule(self, tmpdir):
        input_code = """
        from graphql_server.flask import GraphQLView
        from flask import Flask
        from .schemas import schema
        from graphene.validation import DisableIntrospection

        GraphQLView(
            name="api",
            schema=schema,
            validation_rules = [DisableIntrospection],
        )
        """
        self.run_and_assert(tmpdir, input_code, input_code)
