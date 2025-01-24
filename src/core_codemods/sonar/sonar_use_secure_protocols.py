import libcst as cst
from libcst.codemod import CodemodContext

from codemodder.codemods.base_codemod import (
    Metadata,
    ReviewGuidance,
    ToolMetadata,
    ToolRule,
)
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameAndAncestorResolutionMixin
from codemodder.codetf import Reference
from codemodder.file_context import FileContext
from codemodder.result import Result
from core_codemods.sonar.api import SonarCodemod

rules = [
    ToolRule(
        id="python:S5332",
        name="Using clear-text protocols is security-sensitive",
        url="https://rules.sonarsource.com/python/RSPEC-5332/",
    ),
]


class SonarUseSecureProtocolsTransformer(
    LibcstResultTransformer, NameAndAncestorResolutionMixin
):
    change_description = "Modified URLs or calls to use secure protocols"

    def __init__(
        self,
        context: CodemodContext,
        results: list[Result] | None,
        file_context: FileContext,
        _transformer: bool = False,
    ):
        self.nodes_memory_with_context_name: dict[cst.CSTNode, str] = {}
        super().__init__(context, results, file_context, _transformer)

    def _match_and_handle_statement(
        self, possible_smtp_call, original_node_statement, updated_node_statement
    ):
        maybe_name = self.find_base_name(possible_smtp_call)
        match possible_smtp_call:
            case cst.Call() if maybe_name == "smtplib.SMTP":
                # get the stored context_name or create a new one:
                if possible_smtp_call in self.nodes_memory_with_context_name:
                    context_name = self.nodes_memory_with_context_name[
                        possible_smtp_call
                    ]
                else:
                    context_name = self.generate_available_name(
                        original_node_statement, ["smtp_context"]
                    )

                new_statements = []
                new_statements.append(
                    cst.parse_statement(
                        f"{context_name} = ssl.create_default_context()"
                    )
                )
                new_statements.append(
                    cst.parse_statement(
                        f"{context_name}.verify_mode = ssl.CERT_REQUIRED"
                    )
                )
                new_statements.append(
                    cst.parse_statement(f"{context_name}.check_hostname = True")
                )
                new_statements.append(updated_node_statement)
                # don't append this if we changed the call to SSL version
                if possible_smtp_call in self.nodes_memory_with_context_name:
                    self.nodes_memory_with_context_name.pop(possible_smtp_call)
                else:
                    new_statements.append(
                        cst.parse_statement(f"smtplib.starttls(context={context_name})")
                    )
                self.add_needed_import("smtplib")
                self.add_needed_import("ssl")
                self.report_change(possible_smtp_call)
                return cst.FlattenSentinel(new_statements)
        return updated_node_statement

    def leave_SimpleStatementLine(self, original_node, updated_node):
        match original_node.body:
            # match the first statement that is either selected or is an assignment whose value is selected
            case [cst.Assign() as a, *_] if self.node_is_selected(a.value):
                return self._match_and_handle_statement(
                    a.value, original_node, updated_node
                )
            case [s, *_] if self.node_is_selected(s):
                return self._match_and_handle_statement(s, original_node, updated_node)
        return updated_node

    def leave_Call(self, original_node, updated_node):
        if self.node_is_selected(original_node):
            match self.find_base_name(original_node):
                case "ftplib.FTP":
                    new_func = cst.parse_expression("ftplib.FTP_TLS")
                    self.report_change(original_node)
                    self.add_needed_import("ftplib")
                    return updated_node.with_changes(func=new_func)
                # Just using ssl.create_default_context() may not be enough for older python versions
                # See https://stackoverflow.com/questions/33857698/sending-email-from-python-using-starttls
                case "smtplib.SMTP":
                    # port is the second positional, check that
                    maybe_port_value = (
                        original_node.args[1]
                        if len(original_node.args) >= 2
                        and original_node.args[1].keyword is None
                        else None
                    )
                    # find port keyword, if any
                    maybe_port_value = maybe_port_value or next(
                        iter(
                            [
                                a
                                for a in original_node.args
                                if a.keyword and a.keyword.value == "port"
                            ]
                        ),
                        None,
                    )
                    maybe_port_value = (
                        maybe_port_value.value if maybe_port_value else None
                    )
                    match maybe_port_value:
                        case None:
                            return self._change_to_smtp_ssl(original_node, updated_node)
                        case cst.Integer() if maybe_port_value.value == "0":
                            return self._change_to_smtp_ssl(original_node, updated_node)
        return updated_node

    def _change_to_smtp_ssl(self, original_node, updated_node):
        # remember this node so we don't add the starttls
        new_func = cst.parse_expression("smtplib.SMTP_SSL")

        context_name = self.generate_available_name(original_node, ["smtp_context"])
        self.nodes_memory_with_context_name[original_node] = context_name

        new_args = [
            *original_node.args,
            cst.Arg(
                keyword=cst.Name("context"),
                value=cst.Name(context_name),
            ),
        ]
        return updated_node.with_changes(func=new_func, args=new_args)

    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> cst.BaseExpression:
        if self.node_is_selected(original_node):
            match original_node.raw_value:
                case original_node.raw_value as s if s.startswith("http"):
                    self.report_change(original_node)
                    return updated_node.with_changes(
                        value=original_node.prefix
                        + original_node.quote
                        + s.replace("http", "https", 1)
                        + original_node.quote
                    )
                case original_node.raw_value as s if s.startswith("ftp"):
                    self.report_change(original_node)
                    return updated_node.with_changes(
                        value=original_node.prefix
                        + original_node.quote
                        + s.replace("ftp", "sftp", 1)
                        + original_node.quote
                    )
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
        ]
        + [Reference(url=tr.url or "", description=tr.name) for tr in rules],
        tool=ToolMetadata(
            name="Sonar",
            rules=rules,
        ),
    ),
    transformer=LibcstTransformerPipeline(SonarUseSecureProtocolsTransformer),
    default_extensions=[".py"],
    requested_rules=[tr.id for tr in rules],
)
