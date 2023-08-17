from codemodder.codemods.django_debug_flag_on import DjangoDebugFlagOn
from codemodder.codemods.django_session_cookie_secure_off import (
    DjangoSessionCookieSecureOff,
)
from codemodder.codemods.harden_pyyaml import HardenPyyaml
from codemodder.codemods.limit_readline import LimitReadline
from codemodder.codemods.secure_random import SecureRandom
from codemodder.codemods.url_sandbox import UrlSandbox
from codemodder.codemods.process_creation_sandbox import ProcessSandbox
from codemodder.codemods.remove_unnecessary_f_str import RemoveUnnecessaryFStr

DEFAULT_CODEMODS = {
    DjangoDebugFlagOn,
    DjangoSessionCookieSecureOff,
    HardenPyyaml,
    LimitReadline,
    ProcessSandbox,
    RemoveUnnecessaryFStr,
    SecureRandom,
    UrlSandbox,
}
ALL_CODEMODS = DEFAULT_CODEMODS


def match_codemods(codemod_include: list, codemod_exclude: list) -> dict:
    if not codemod_include and not codemod_exclude:
        return {codemod.METADATA.NAME: codemod for codemod in DEFAULT_CODEMODS}

    # cli should've already prevented both include/exclude from being set.
    assert codemod_include or codemod_exclude

    if codemod_exclude:
        return {
            name: codemod
            for codemod in DEFAULT_CODEMODS
            if (name := codemod.METADATA.NAME) not in codemod_exclude
        }

    return {
        name: codemod
        for codemod in DEFAULT_CODEMODS
        if (name := codemod.METADATA.NAME) in codemod_include
    }
