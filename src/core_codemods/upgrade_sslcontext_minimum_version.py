from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class UpgradeSSLContextMinimumVersion(SemgrepCodemod):
    NAME = "upgrade-sslcontext-minimum-version"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Upgrade minimum SSL/TLS version for SSLContext"
    DESCRIPTION = "Replaces minimum SSL/TLS version for SSLContext"
    REFERENCES = [
        {
            "url": "https://docs.python.org/3/library/ssl.html#security-considerations",
            "description": "",
        },
        {"url": "https://datatracker.ietf.org/doc/rfc8996/", "description": ""},
        {
            "url": "https://www.digicert.com/blog/depreciating-tls-1-0-and-1-1",
            "description": "",
        },
    ]

    @classmethod
    def rule(cls):
        return """
        rules:
          - mode: taint
            pattern-sources:
              - patterns:
                - pattern: ssl.SSLContext(...)
                - pattern-inside: |
                    import ssl
                    ...
            pattern-sinks:
              - patterns:
                - pattern: $SINK.minimum_version = ssl.TLSVersion.$VERSION
                - metavariable-pattern:
                    metavariable: $VERSION
                    patterns:
                      - pattern-either:
                        - pattern: SSLv2
                        - pattern: SSLv3
                        - pattern: TLSv1
                        - pattern: TLSv1_1
                        - pattern: MINIMUM_SUPPORTED
        """

    def on_result_found(self, original_node, updated_node):
        self.remove_unused_import(original_node)
        self.add_needed_import("ssl")
        return self.update_assign_rhs(updated_node, "ssl.TLSVersion.TLSv1_2")
