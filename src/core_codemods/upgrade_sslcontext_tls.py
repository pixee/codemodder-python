from codemodder.codemods.libcst_transformer import NewArg
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class UpgradeSSLContextTLS(SimpleCodemod):
    metadata = Metadata(
        name="upgrade-sslcontext-tls",
        summary="Upgrade TLS Version In SSLContext",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/ssl.html#security-considerations"
            ),
            Reference(url="https://datatracker.ietf.org/doc/rfc8996/"),
            Reference(url="https://www.digicert.com/blog/depreciating-tls-1-0-and-1-1"),
        ],
    )
    change_description = "Replaces known insecure TLS/SSL protocol versions in SSLContext with secure ones."
    change_description = "Upgrade to use a safe version of TLS in SSLContext"

    # TODO: in the majority of cases, using PROTOCOL_TLS_CLIENT will be the
    # right fix. However in some cases it will be appropriate to use
    # PROTOCOL_TLS_SERVER instead. We currently don't have a good way to handle
    # this. Eventually, when the platform supports parameters, we want to
    # revisit this to provide PROTOCOL_TLS_SERVER as an alternative fix.
    SAFE_TLS_PROTOCOL_VERSION = "ssl.PROTOCOL_TLS_CLIENT"
    detector_pattern = """
            rules:
              - patterns:
                - pattern-inside: |
                      import ssl
                      ...
                - pattern-either:
                    - pattern: ssl.SSLContext()
                    - pattern: ssl.SSLContext(...,ssl.PROTOCOL_SSLv2,...)
                    - pattern: ssl.SSLContext(...,protocol=ssl.PROTOCOL_SSLv2,...)
                    - pattern: ssl.SSLContext(...,ssl.PROTOCOL_SSLv3,...)
                    - pattern: ssl.SSLContext(...,protocol=ssl.PROTOCOL_SSLv3,...)
                    - pattern: ssl.SSLContext(...,ssl.PROTOCOL_TLSv1,...)
                    - pattern: ssl.SSLContext(...,protocol=ssl.PROTOCOL_TLSv1,...)
                    - pattern: ssl.SSLContext(...,ssl.PROTOCOL_TLSv1_1,...)
                    - pattern: ssl.SSLContext(...,protocol=ssl.PROTOCOL_TLSv1_1,...)
                    - pattern: ssl.SSLContext(...,ssl.PROTOCOL_TLS,...)
                    - pattern: ssl.SSLContext(...,protocol=ssl.PROTOCOL_TLS,...)
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("ssl")

        if len((args := original_node.args)) == 1 and args[0].keyword is None:
            new_args = [self.make_new_arg(self.SAFE_TLS_PROTOCOL_VERSION)]
        else:
            new_args = self.replace_args(
                original_node,
                [
                    NewArg(
                        name="protocol",
                        value=self.SAFE_TLS_PROTOCOL_VERSION,
                        add_if_missing=True,
                    )
                ],
            )
        return self.update_arg_target(updated_node, new_args)
