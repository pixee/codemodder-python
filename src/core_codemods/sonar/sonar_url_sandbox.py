from core_codemods.sonar.api import SonarCodemod
from core_codemods.url_sandbox import UrlSandbox

SonarUrlSandbox = SonarCodemod.from_core_codemod(
    name="url-sandbox",
    other=UrlSandbox,
    rule_id="pythonsecurity:S5144",
    rule_name="Server-side requests should not be vulnerable to forging attacks",
)
