from codemodder.codemods.secure_random import SecureRandom
from codemodder.codemods.url_sandbox import UrlSandbox

DEFAULT_CODEMODS = {SecureRandom, UrlSandbox}


def match_codemods(codemod_include: list, codemod_exclude: list):
    if not codemod_include and not codemod_exclude:
        return {codemod.NAME: codemod for codemod in DEFAULT_CODEMODS}

    # cli should've already prevented both include/exclude from being set.
    assert codemod_include or codemod_exclude

    if codemod_exclude:
        return {
            name: codemod
            for codemod in DEFAULT_CODEMODS
            if (name := codemod.NAME) not in codemod_exclude
        }
    if codemod_include:
        return {
            name: codemod
            for codemod in DEFAULT_CODEMODS
            if (name := codemod.NAME) in codemod_include
        }
    return {}
