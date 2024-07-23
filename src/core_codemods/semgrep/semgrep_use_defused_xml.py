from core_codemods.semgrep.api import SemgrepCodemod, ToolRule, semgrep_url_from_id
from core_codemods.use_defused_xml import UseDefusedXml

SemgrepUseDefusedXml = SemgrepCodemod.from_core_codemod(
    name="use-defusedxml",
    other=UseDefusedXml,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.lang.security.use-defused-xml-parse.use-defused-xml-parse"
            ),
            name="use-defused-xml-parse",
            url=semgrep_url_from_id(rule_id),
        )
    ],
)
