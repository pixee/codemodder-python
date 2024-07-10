from core_codemods.enable_jinja2_autoescape import EnableJinja2Autoescape
from core_codemods.sonar.api import SonarCodemod

SonarEnableJinja2Autoescape = SonarCodemod.from_core_codemod(
    name="enable-jinja2-autoescape",
    other=EnableJinja2Autoescape,
    rule_id="python:S5247",
    rule_name="Disabling auto-escaping in template engines is security-sensitive",
)
