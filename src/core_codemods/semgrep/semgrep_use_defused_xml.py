from core_codemods.semgrep.api import SemgrepCodemod
from core_codemods.use_defused_xml import UseDefusedXml

SemgrepUseDefusedXml = SemgrepCodemod.from_import_modifier_codemod(
    name="use-defusedxml",
    other=UseDefusedXml,
    rule_id="python.lang.security.use-defused-xml-parse.use-defused-xml-parse",
    rule_name="use-defused-xml-parse",
)
