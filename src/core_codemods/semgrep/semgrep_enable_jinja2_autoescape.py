from core_codemods.enable_jinja2_autoescape import EnableJinja2Autoescape
from core_codemods.semgrep.api import SemgrepCodemod

SemgrepEnableJinja2Autoescape = SemgrepCodemod.from_core_codemod(
    name="enable-jinja2-autoescape",
    other=EnableJinja2Autoescape,
    rule_id="python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2",
    rule_name="direct-use-of-jinja2",
)
