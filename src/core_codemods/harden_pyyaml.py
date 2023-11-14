from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.utils_mixin import NameResolutionMixin


class HardenPyyaml(SemgrepCodemod, NameResolutionMixin):
    NAME = "harden-pyyaml"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Use SafeLoader in `yaml.load()` Calls"
    DESCRIPTION = "Ensures all calls to yaml.load use `SafeLoader`."
    REFERENCES = [
        {
            "url": "https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data",
            "description": "",
        }
    ]

    _module_name = "yaml"

    @classmethod
    def rule(cls):
        return """
            rules:
                - pattern-either:
                  - patterns:
                      - pattern: yaml.load(...)
                      - pattern-inside: |
                          import yaml
                          ...
                          yaml.load(...,$ARG)
                      - metavariable-pattern:
                          metavariable: $ARG
                          patterns:
                            - pattern-either:
                                - pattern: yaml.Loader
                                - pattern: yaml.BaseLoader
                                - pattern: yaml.FullLoader
                                - pattern: yaml.UnsafeLoader
                  - patterns:
                      - pattern: yaml.load(...)
                      - pattern-inside: |
                          import yaml
                          ...
                          yaml.load(...,Loader=$ARG)
                      - metavariable-pattern:
                          metavariable: $ARG
                          patterns:
                            - pattern-either:
                                - pattern: yaml.Loader
                                - pattern: yaml.BaseLoader
                                - pattern: yaml.FullLoader
                                - pattern: yaml.UnsafeLoader

        """

    def on_result_found(self, original_node, updated_node):
        maybe_name = self.get_aliased_prefix_name(original_node, self._module_name)
        maybe_name = maybe_name or self._module_name
        if maybe_name == self._module_name:
            self.add_needed_import(self._module_name)
        new_args = [
            *updated_node.args[:1],
            updated_node.args[1].with_changes(
                value=self.parse_expression(f"{maybe_name}.SafeLoader")
            ),
        ]
        return self.update_arg_target(updated_node, new_args)
