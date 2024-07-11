from codemodder.codemods.base_codemod import ToolRule
from core_codemods.defectdojo.semgrep.django_secure_set_cookie import (
    DjangoSecureSetCookie,
)
from core_codemods.semgrep.api import SemgrepCodemod, semgrep_url_from_id

SemgrepDjangoSecureSetCookie = SemgrepCodemod.from_core_codemod(
    name="django-secure-set-cookie",
    other=DjangoSecureSetCookie,
    rules=[
        ToolRule(
            id=(
                rule_id := "python.django.security.audit.secure-cookies.django-secure-set-cookie"
            ),
            name="django-secure-set-cookie",
            url=semgrep_url_from_id(rule_id),
        )
    ],
)
