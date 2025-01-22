from codemodder.codemods.base_codemod import Metadata, ReviewGuidance, ToolRule
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codetf import Reference
from core_codemods.sonar.api import SonarCodemod

rules = [
    ToolRule(
        id="python:S5332",
        name="Using clear-text protocols is security-sensitive",
        url="https://rules.sonarsource.com/python/RSPEC-5332/",
    ),
]


class SonarUseSecureProtocolsTransformer(LibcstResultTransformer):
    change_description = "Modified URLs or calls to use secure protocols"

    def leave_Call(self, original_node, updated_node):
        return updated_node


SonarUseSecureProtocols = SonarCodemod(
    metadata=Metadata(
        name="use-secure-protocols",
        summary="Use encrypted protocols instead of clear-text",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/ftplib.html#ftplib.FTP_TLS"
            ),
            Reference(
                url="https://docs.python.org/3/library/smtplib.html#smtplib.SMTP.starttls"
            ),
            Reference(url="https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"),
            Reference(
                url="https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure"
            ),
            Reference(url="https://cwe.mitre.org/data/definitions/200"),
            Reference(url="https://cwe.mitre.org/data/definitions/319"),
        ],
    ),
    transformer=LibcstTransformerPipeline(SonarUseSecureProtocolsTransformer),
    default_extensions=[".py"],
    requested_rules=[tr.id for tr in rules],
)
