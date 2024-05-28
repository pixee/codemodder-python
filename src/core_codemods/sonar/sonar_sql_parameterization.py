from core_codemods.sonar.api import SonarCodemod
from core_codemods.sql_parameterization import SQLQueryParameterization

SonarSQLParameterization = SonarCodemod.from_core_codemod(
    name="sql-parameterization-S3649",
    other=SQLQueryParameterization,
    rule_id="pythonsecurity:S3649",
    rule_name="Database queries should not be vulnerable to injection attacks",
)
