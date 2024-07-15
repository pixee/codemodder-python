from codemodder.codemods.base_codemod import ToolRule
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id
from core_codemods.sql_parameterization import SQLQueryParameterization

SemgrepSQLParameterization = SemgrepCodemod.from_core_codemod(
    name="sql-parameterization",
    other=SQLQueryParameterization,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.django.security.injection.sql.sql-injection-using-db-cursor-execute.sql-injection-db-cursor-execute"
            ),
            name="sql-injection-db-cursor-execute",
            url=semgrep_url_from_id(rule_id),
        ),
        ToolRule(
            id=(
                rule_id := "python.lang.security.audit.formatted-sql-query.formatted-sql-query"
            ),
            name="formatted-sql-query",
            url=semgrep_url_from_id(rule_id),
        ),
        ToolRule(
            id=(
                rule_id := "python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query"
            ),
            name="sqlalchemy-execute-raw-query",
            url=semgrep_url_from_id(rule_id),
        ),
        ToolRule(
            id=(
                rule_id := "python.django.security.injection.tainted-sql-string.tainted-sql-string"
            ),
            name="tainted-sql-string",
            url=semgrep_url_from_id(rule_id),
        ),
        ToolRule(
            id=(
                rule_id := "python.flask.security.injection.tainted-sql-string.tainted-sql-string"
            ),
            name="tainted-sql-string",
            url=semgrep_url_from_id(rule_id),
        ),
    ],
)
