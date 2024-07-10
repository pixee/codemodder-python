from core_codemods.disable_graphql_introspection import DisableGraphQLIntrospection
from core_codemods.sonar.api import SonarCodemod

SonarDisableGraphQLIntrospection = SonarCodemod.from_core_codemod(
    name="disable-graphql-introspection",
    other=DisableGraphQLIntrospection,
    rule_id="python:S6786",
    rule_name="GraphQL introspection should be disabled in production",
)
