from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import Metadata, Reference, ReviewGuidance, SimpleCodemod


class UpgradeSSLContextMinimumVersion(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="upgrade-sslcontext-minimum-version",
        summary="Upgrade SSLContext Minimum Version",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://docs.python.org/3/library/ssl.html#security-considerations"
            ),
            Reference(url="https://datatracker.ietf.org/doc/rfc8996/"),
            Reference(url="https://www.digicert.com/blog/depreciating-tls-1-0-and-1-1"),
        ],
    )
    change_description = "Replaces minimum SSL/TLS version for SSLContext."

    _module_name = "ssl"
    detector_pattern = """
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
        if (maybe_name := maybe_name or self._module_name) == self._module_name:
            self.add_needed_import(self._module_name)
        self.remove_unused_import(original_node)
        return self.update_assign_rhs(updated_node, f"{maybe_name}.TLSVersion.TLSv1_2")
