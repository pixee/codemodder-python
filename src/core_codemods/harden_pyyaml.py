from typing import Protocol, Union, cast

import libcst as cst

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.api import CoreCodemod, Metadata, Reference, ReviewGuidance

YAML_MODULE_NAME = "yaml"


class CodemodProtocol(Protocol):
    def add_needed_import(self, module: str, obj=None): ...
    def get_aliased_prefix_name(self, node: cst.CSTNode, module: str): ...
    def parse_expression(self, code: str) -> cst.BaseExpression: ...
    def update_arg_target(
        self, node: cst.Call, new_args: list[cst.Arg]
    ) -> cst.Call: ...


class HardenPyyamlCallMixin:
    def update_call(
        self: CodemodProtocol,
        original_node: cst.Call,
        updated_node: cst.Call,
        maybe_aliased_name: str | None = None,
    ) -> cst.Call:
        module_name = maybe_aliased_name or YAML_MODULE_NAME
        if not maybe_aliased_name:
            self.add_needed_import(YAML_MODULE_NAME)

        updated_node = cast(cst.Call, updated_node)  # satisfy the type checker
        new_args = [
            *updated_node.args[:1],
            # This is the case where the arg is present but a bad value
            (
                updated_node.args[1].with_changes(
                    value=self.parse_expression(f"{module_name}.SafeLoader")
                )
                if len(updated_node.args) > 1
                # This is the case where the arg is not present
                # Note that this case is deprecated in PyYAML 5.1 since the default is unsafe
                else cst.Arg(
                    keyword=cst.Name("Loader"),
                    value=self.parse_expression(f"{module_name}.SafeLoader"),
                    equal=cst.AssignEqual(
                        whitespace_before=cst.SimpleWhitespace(""),
                        whitespace_after=cst.SimpleWhitespace(""),
                    ),
                )
            ),
        ]
        return self.update_arg_target(updated_node, new_args)


class HardenPyyamlTransformer(
    LibcstResultTransformer,
    NameResolutionMixin,
    HardenPyyamlCallMixin,
    CodemodProtocol,
):
    change_description = "Replace unsafe `pyyaml` loader with `SafeLoader` in calls to `yaml.load` or custom loader classes."

    def on_result_found(
        self,
        original_node: Union[cst.Call, cst.ClassDef],
        updated_node: Union[cst.Call, cst.ClassDef],
    ):
        # TODO: provide different change description for each case.
        maybe_aliased_name = self.get_aliased_prefix_name(
            original_node, YAML_MODULE_NAME
        )
        match original_node, updated_node:
            case cst.Call(), cst.Call():
                return self.update_call(original_node, updated_node, maybe_aliased_name)
            case cst.ClassDef(), _:
                return updated_node.with_changes(
                    bases=self._update_bases(original_node, maybe_aliased_name)
                )
        return updated_node

    def _update_bases(
        self, original_node: cst.ClassDef, maybe_aliased_name: str | None = None
    ) -> list[cst.Arg]:
        new = []
        base_names = [
            f"yaml.{klas}"
            for klas in ("UnsafeLoader", "Loader", "BaseLoader", "FullLoader")
        ]
        module_name = maybe_aliased_name or YAML_MODULE_NAME
        for base_arg in original_node.bases:
            base_name = self.find_base_name(base_arg.value)
            if base_name not in base_names:
                new.append(base_arg)
                continue

            match base_arg.value:
                case cst.Name():
                    if not maybe_aliased_name:
                        self.add_needed_import(module_name, "SafeLoader")
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


HardenPyyaml = CoreCodemod(
    metadata=Metadata(
        name="harden-pyyaml",
        summary="Replace unsafe `pyyaml` loader with `SafeLoader`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(
                url="https://owasp.org/www-community/vulnerabilities/Deserialization_of_untrusted_data"
            ),
            Reference(
                url="https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation"
            ),
        ],
    ),
    detector=SemgrepRuleDetector(
        """
        rules:
            - pattern-either:
              - patterns:
                  - pattern: yaml.load(...)
                  - pattern-inside: |
                      import yaml
                      ...
                      yaml.load($ARG)
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
    ),
    transformer=LibcstTransformerPipeline(HardenPyyamlTransformer),
)
