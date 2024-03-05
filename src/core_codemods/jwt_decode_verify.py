import libcst as cst
from libcst import matchers

from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
    NewArg,
)
from codemodder.codemods.semgrep import SemgrepRuleDetector
from core_codemods.api import Metadata, Reference, ReviewGuidance
from core_codemods.api.core_codemod import CoreCodemod


class JwtDecodeVerifyTransformer(LibcstResultTransformer):
    change_description = "Enable all verifications in `jwt.decode` call."

    def _replace_opts_dict(self, opts_dict):
        new_dict_elements = []

        for element in opts_dict.elements:
            if is_verify_keyword(element):
                new_el = cst.DictElement(
                    key=cst.parse_expression(element.key.value),
                    value=cst.parse_expression("True"),
                )
            else:
                new_el = element
            new_dict_elements.append(new_el)
        return new_dict_elements

    def replace_options_arg(self, node_args):
        new_args = []
        for arg in node_args:
            if matchers.matches(arg.keyword, matchers.Name("options")) and isinstance(
                opts_dict := arg.value, cst.Dict
            ):
                new_dict_elements = self._replace_opts_dict(opts_dict)
                new = cst.Arg(
                    keyword=cst.parse_expression("options"),
                    value=cst.Dict(
                        elements=new_dict_elements,
                    ),
                    equal=arg.equal,
                )
            else:
                new = arg
            new_args.append(new)
        return new_args

    def replace_args(self, original_node, args_info):
        new_args = super().replace_args(original_node, args_info)
        return self.replace_options_arg(new_args)

    def on_result_found(self, original_node, updated_node):
        new_args = self.replace_args(
            original_node, [NewArg(name="verify", value="True", add_if_missing=False)]
        )
        return self.update_arg_target(updated_node, new_args)


def is_verify_keyword(element: cst.DictElement) -> bool:
    """Determine if DictElement is something like:
        DictElement(
            key=SimpleString(
                value='"verify_signature"',
                lpar=[],
                rpar=[],
            )
            ...
    where value should be anything with the word `verify`
    """
    return (
        matchers.matches(element.key, matchers.SimpleString())
        and "verify" in element.key.value
    )


JwtDecodeVerify = CoreCodemod(
    metadata=Metadata(
        name="jwt-decode-verify",
        summary="Verify JWT Decode",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
        references=[
            Reference(url="https://pyjwt.readthedocs.io/en/stable/api.html"),
            Reference(
                url="https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/06-Session_Management_Testing/10-Testing_JSON_Web_Tokens"
            ),
        ],
    ),
    transformer=LibcstTransformerPipeline(JwtDecodeVerifyTransformer),
    detector=SemgrepRuleDetector(
        r"""
            rules:
                - pattern-either:
                  - patterns:
                      - pattern: jwt.decode(..., verify=False, ...)
                      - pattern-inside: |
                          import jwt
                          ...
                  - patterns:
                      - pattern: |
                          jwt.decode(..., options={..., "$KEY": False, ...}, ...)
                      - metavariable-regex:
                          metavariable: $KEY
                          regex: verify_
                      - pattern-inside: |
                          import jwt
                            ...
        """
    ),
)
