import libcst as cst

from codemodder.codemods.api import Metadata, ReviewGuidance, ToolMetadata, ToolRule
from codemodder.codemods.libcst_transformer import (
    LibcstResultTransformer,
    LibcstTransformerPipeline,
)
from codemodder.codemods.utils_mixin import NameResolutionMixin
from core_codemods.defectdojo.api import DefectDojoCodemod, DefectDojoDetector
from core_codemods.secure_cookie_mixin import SecureCookieMixin


class DjangoSecureSetCookieTransformer(
    LibcstResultTransformer,
    NameResolutionMixin,
    SecureCookieMixin,
):
    change_description = (
        "Call `set_cookie` with `secure=True`, `httponly=True`, and `samesite='Lax'."
    )

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if self.node_is_selected(original_node):
            if (name := self.find_base_name(original_node.func)) and name.endswith(
                "set_cookie"
            ):
                new_args = self.replace_args(
                    original_node,
                    self._choose_new_args(original_node),
                )
                self.report_change(original_node)
                return self.update_arg_target(updated_node, new_args)

        return updated_node


DjangoSecureSetCookie = DefectDojoCodemod(
    metadata=Metadata(
        name="django-secure-set-cookie",
        summary="Use Safe Parameters in Django Response `set_cookie` Call",
        review_guidance=ReviewGuidance.MERGE_AFTER_CURSORY_REVIEW,
        tool=ToolMetadata(
            name="DefectDojo",
            rules=[
                ToolRule(
                    id="python.django.security.audit.secure-cookies.django-secure-set-cookie",
                    name="django-secure-set-cookie",
                    url="https://semgrep.dev/playground/r/python.django.security.audit.secure-cookies.django-secure-set-cookie",
                )
            ],
        ),
        references=[],
    ),
    transformer=LibcstTransformerPipeline(DjangoSecureSetCookieTransformer),
    detector=DefectDojoDetector(),
)
