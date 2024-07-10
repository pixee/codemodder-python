from codemodder.codemods.base_codemod import ToolRule
from core_codemods.enable_jinja2_autoescape import EnableJinja2Autoescape
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id

SemgrepEnableJinja2Autoescape = SemgrepCodemod.from_core_codemod(
    name="enable-jinja2-autoescape",
    other=EnableJinja2Autoescape,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2"
            ),
            name="direct-use-of-jinja2",
            url=semgrep_url_from_id(rule_id),
        )
    ],
)
