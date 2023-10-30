from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.utils_mixin import NameResolutionMixin


class UpgradeSSLContextMinimumVersion(SemgrepCodemod, NameResolutionMixin):
    NAME = "upgrade-sslcontext-minimum-version"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Upgrade SSLContext Minimum Version"
    DESCRIPTION = "Replaces minimum SSL/TLS version for SSLContext."
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

    _module_name = "ssl"

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
        maybe_name = self.get_aliased_prefix_name(
            original_node.value, self._module_name
        )
        maybe_name = maybe_name or self._module_name
        if maybe_name == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)
        return self.update_assign_rhs(updated_node, f"{maybe_name}.TLSVersion.TLSv1_2")
