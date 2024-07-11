from codemodder.codemods.base_codemod import ToolRule
from core_codemods.harden_pyyaml import HardenPyyaml
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id

SemgrepHardenPyyaml = SemgrepCodemod.from_core_codemod(
    name="harden-pyyaml",
    other=HardenPyyaml,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load"
            ),
            name=" avoid-pyyaml-load",
            url=semgrep_url_from_id(rule_id),
        ),
        ToolRule(
            id=(
                rule_id := "python.django.security.audit.avoid-insecure-deserialization.avoid-insecure-deserialization"
            ),
            name="avoid-insecure-deserialization",
            url=semgrep_url_from_id(rule_id),
        ),
    ],
)
