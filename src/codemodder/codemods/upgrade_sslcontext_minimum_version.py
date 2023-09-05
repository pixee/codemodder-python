from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod


class UpgradeSSLContextMinimumVersion(SemgrepCodemod):
    NAME = "upgrade-sslcontext-minimum-version"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    DESCRIPTION = "Replaces minimum SSL/TLS version for SSLContext"

    @classmethod
    def rule(cls):
        return """
        rules:
          - patterns:
            - pattern: |
                $CONTEXT.minimum_version = ssl.TLSVersion.$VERSION
            - pattern-inside: |
                import ssl
                ...
                $CONTEXT = ssl.SSLContext(...)
                ...
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
