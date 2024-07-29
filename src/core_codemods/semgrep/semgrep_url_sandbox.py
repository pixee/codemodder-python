from core_codemods.semgrep.api import SemgrepCodemod, ToolRule, semgrep_url_from_id
from core_codemods.url_sandbox import UrlSandbox

SemgrepUrlSandbox = SemgrepCodemod.from_core_codemod(
    name="url-sandbox",
    other=UrlSandbox,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.django.security.injection.ssrf.ssrf-injection-requests.ssrf-injection-requests"
            ),
            name="ssrf-injection-requests",
            url=semgrep_url_from_id(rule_id),
        ),
        ToolRule(
            id=(
                rule_id := "python.flask.security.injection.ssrf-requests.ssrf-requests"
            ),
            name="ssrf-requests",
            url=semgrep_url_from_id(rule_id),
        ),
    ],
)
