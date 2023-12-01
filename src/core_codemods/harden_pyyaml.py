from typing import Union
import libcst as cst
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.api import SemgrepCodemod
from codemodder.codemods.utils_mixin import NameResolutionMixin


class HardenPyyaml(SemgrepCodemod, NameResolutionMixin):
    NAME = "harden-pyyaml"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Replace unsafe `pyyaml` loader with `SafeLoader`"
    DESCRIPTION = "Replace unsafe `pyyaml` loader with `SafeLoader` in calls to `yaml.load` or custom loader classes."
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
                  - patterns:
                      - pattern: |
                          class $X(...,$LOADER, ...):
                            ...
                      - metavariable-pattern:
                          metavariable: $LOADER
                          patterns:
                            - pattern-either:
                                - pattern: yaml.Loader
                                - pattern: yaml.BaseLoader
                                - pattern: yaml.FullLoader
                                - pattern: yaml.UnsafeLoader

        """

    def on_result_found(
        self,
        original_node: Union[cst.Call, cst.ClassDef],
        updated_node: Union[cst.Call, cst.ClassDef],
    ):
        # TODO: provide different change description for each case.
        match original_node:
            case cst.Call():
                maybe_name = self.get_aliased_prefix_name(
                    original_node, self._module_name
                )
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
            case cst.ClassDef():
                return updated_node.with_changes(
                    bases=self._update_bases(original_node)
                )
        return updated_node

    def _update_bases(self, original_node: cst.ClassDef) -> list[cst.Arg]:
        new = []
        base_names = [
            f"yaml.{klas}"
            for klas in ("UnsafeLoader", "Loader", "BaseLoader", "FullLoader")
        ]
        for base_arg in original_node.bases:
            base_name = self.find_base_name(base_arg.value)
            if base_name not in base_names:
                new.append(base_arg)
                continue

            match base_arg.value:
                case cst.Name():
                    self.add_needed_import(self._module_name, "SafeLoader")
                    self.remove_unused_import(base_arg.value)
                    base_arg = base_arg.with_changes(
                        value=base_arg.value.with_changes(value="SafeLoader")
                    )
                case cst.Attribute():
                    base_arg = base_arg.with_changes(
                        value=base_arg.value.with_changes(attr=cst.Name("SafeLoader"))
                    )
            new.append(base_arg)
        return new
