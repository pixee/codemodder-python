from codemodder.codemods.secure_random import SecureRandom
from codemodder.codemods.url_sandbox import UrlSandbox


CODEMODS = {"secure-random": SecureRandom, "url-sandbox": UrlSandbox}


def match_codemods(codemod_include: list, codemod_exclude: list):
    if not codemod_include and not codemod_exclude:
        return CODEMODS

    # cli should've already prevented both include/exclude from being set.
    assert codemod_include or codemod_exclude

    if codemod_exclude:
        return {
            name: codemod
            for (name, codemod) in CODEMODS.items()
            if name not in codemod_exclude
        }
    if codemod_include:
        return {
            name: codemod
            for (name, codemod) in CODEMODS.items()
            if name in codemod_include
        }
    return {}
