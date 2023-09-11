from codemodder.codemods.order_imports import OrderImports
from codemodder.codemods.remove_unused_imports import RemoveUnusedImports
from codemodder.codemods.django_debug_flag_on import DjangoDebugFlagOn
from codemodder.codemods.django_session_cookie_secure_off import (
    DjangoSessionCookieSecureOff,
)
from codemodder.codemods.harden_pyyaml import HardenPyyaml
from codemodder.codemods.harden_ruamel import HardenRuamel
from codemodder.codemods.https_connection import HTTPSConnection
from codemodder.codemods.limit_readline import LimitReadline
from codemodder.codemods.secure_random import SecureRandom
from codemodder.codemods.upgrade_sslcontext_tls import UpgradeSSLContextTLS
from codemodder.codemods.upgrade_sslcontext_minimum_version import (
    UpgradeSSLContextMinimumVersion,
)
from codemodder.codemods.url_sandbox import UrlSandbox
from codemodder.codemods.process_creation_sandbox import ProcessSandbox
from codemodder.codemods.remove_unnecessary_f_str import RemoveUnnecessaryFStr
from codemodder.codemods.tempfile_mktemp import TempfileMktemp
from codemodder.codemods.requests_verify import RequestsVerify

DEFAULT_CODEMODS = {
    DjangoDebugFlagOn,
    DjangoSessionCookieSecureOff,
    HardenPyyaml,
    HardenRuamel,
    HTTPSConnection,
    LimitReadline,
    OrderImports,
    ProcessSandbox,
    RemoveUnnecessaryFStr,
    RemoveUnusedImports,
    SecureRandom,
    UpgradeSSLContextTLS,
    UpgradeSSLContextMinimumVersion,
    UrlSandbox,
    TempfileMktemp,
    RequestsVerify,
}
ALL_CODEMODS = DEFAULT_CODEMODS

CODEMOD_IDS = [codemod.id() for codemod in DEFAULT_CODEMODS]
CODEMOD_NAMES = [codemod.name() for codemod in DEFAULT_CODEMODS]


# TODO: codemod registry


def match_codemods(codemod_include: list, codemod_exclude: list) -> dict:
    if not codemod_include and not codemod_exclude:
        return {codemod.name(): codemod for codemod in DEFAULT_CODEMODS}

    # cli should've already prevented both include/exclude from being set.
    assert codemod_include or codemod_exclude

    if codemod_exclude:
        return {
            name: codemod
            for codemod in DEFAULT_CODEMODS
            if (name := codemod.name()) not in codemod_exclude
            and (_ := codemod.id()) not in codemod_exclude
        }

    return {
        name: codemod
        for codemod in DEFAULT_CODEMODS
        if (name := codemod.name()) in codemod_include
        or (_ := codemod.id()) in codemod_include
    }
