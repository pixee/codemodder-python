from codemodder.codemods.secure_random import SecureRandom
from codemodder.codemods.url_sandbox import UrlSandbox


DEFAULT_CODEMODS = {SecureRandom, UrlSandbox}


def grab_name(codemod):
    """
    Returns the id
    """
    return codemod.full_name().rsplit("/", 1)[-1]


def match_codemods(codemod_include: list, codemod_exclude: list):
    if not codemod_include and not codemod_exclude:
        return {grab_name(codemod): codemod for codemod in DEFAULT_CODEMODS}

    # cli should've already prevented both include/exclude from being set.
    assert codemod_include or codemod_exclude

    if codemod_exclude:
        return {
            name: codemod
            for codemod in DEFAULT_CODEMODS
            if (name := grab_name(codemod)) not in codemod_exclude
        }
    if codemod_include:
        return {
            name: codemod
            for codemod in DEFAULT_CODEMODS
            if (name := grab_name(codemod)) in codemod_include
        }
    return {}
