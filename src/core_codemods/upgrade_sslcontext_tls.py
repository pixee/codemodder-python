import libcst as cst
from libcst.codemod import CodemodContext
from codemodder.codemods.base_visitor import BaseTransformer
from codemodder.codemods.base_codemod import (
    SemgrepCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.change import Change
from codemodder.context import CodemodExecutionContext
from codemodder.file_context import FileContext


class UpgradeSSLContextTLS(SemgrepCodemod, BaseTransformer):
    METADATA = CodemodMetadata(
        DESCRIPTION="Replaces known insecure TLS/SSL protocol versions in SSLContext with secure ones",
        NAME="upgrade-sslcontext-tls",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        REFERENCES=[
            {
                "url": "https://docs.python.org/3/library/ssl.html#security-considerations",
                "description": "",
            },
            {"url": "https://datatracker.ietf.org/doc/rfc8996/", "description": ""},
            {
                "url": "https://www.digicert.com/blog/depreciating-tls-1-0-and-1-1",
                "description": "",
            },
        ],
    )
    SUMMARY = "Replace known insecure TLS/SSL protocol versions in SSLContext with secure ones"
    CHANGE_DESCRIPTION = "Upgrade to use a safe version of TLS in SSLContext"
    YAML_FILES = [
        "upgrade_sslcontext_tls.yaml",
    ]

    # TODO: in the majority of cases, using PROTOCOL_TLS_CLIENT will be the
    # right fix. However in some cases it will be appropriate to use
    # PROTOCOL_TLS_SERVER instead. We currently don't have a good way to handle
    # this. Eventually, when the platform supports parameters, we want to
    # revisit this to provide PROTOCOL_TLS_SERVER as an alternative fix.
    SAFE_TLS_PROTOCOL_VERSION = "PROTOCOL_TLS_CLIENT"
    PROTOCOL_ARG_INDEX = 0
    PROTOCOL_KWARG_NAME = "protocol"

    def __init__(
        self,
        codemod_context: CodemodContext,
        execution_context: CodemodExecutionContext,
        file_context: FileContext,
    ):
        SemgrepCodemod.__init__(self, execution_context, file_context)
        BaseTransformer.__init__(self, codemod_context, self._results)

        # TODO: apply unused import remover

    def update_arg(self, arg: cst.Arg) -> cst.Arg:
        new_name = cst.Name(self.SAFE_TLS_PROTOCOL_VERSION)
        # TODO: are there other cases to handle here?
        new_value = (
            arg.value.with_changes(attr=new_name)
            if isinstance(arg.value, cst.Attribute)
            else new_name
        )
        return arg.with_changes(value=new_value)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Arg):
        pos_to_match = self.get_metadata(self.METADATA_DEPENDENCIES[0], original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            self.file_context.codemod_changes.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )

            return updated_node.with_changes(
                args=[
                    self.update_arg(arg)
                    if idx == self.PROTOCOL_ARG_INDEX
                    or (arg.keyword and arg.keyword.value == self.PROTOCOL_KWARG_NAME)
                    else arg
                    for idx, arg in enumerate(original_node.args)
                ]
            )

        return updated_node
