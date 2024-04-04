from codemodder.codemods.sonar import SonarCodemod
from core_codemods.url_sandbox import UrlSandbox

SonarUrlSandbox = SonarCodemod.from_core_codemod(
    name="url-sandbox-S5144",
    other=UrlSandbox,
    rule_id="pythonsecurity:S5144",
    rule_name="Server-side requests should not be vulnerable to forging attacks",
    rule_url="https://rules.sonarsource.com/python/type/Vulnerability/RSPEC-5144/",
)
