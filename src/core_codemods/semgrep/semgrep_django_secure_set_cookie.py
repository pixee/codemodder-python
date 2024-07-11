from core_codemods.defectdojo.semgrep.django_secure_set_cookie import (
    DjangoSecureSetCookie,
)
from core_codemods.semgrep.api import SemgrepCodemod

SemgrepDjangoSecureSetCookie = SemgrepCodemod.from_core_codemod(
    name="django-secure-set-cookie",
    other=DjangoSecureSetCookie,
    rule_id="python.django.security.audit.secure-cookies.django-secure-set-cookie",
    rule_name="django-secure-set-cookie",
)
