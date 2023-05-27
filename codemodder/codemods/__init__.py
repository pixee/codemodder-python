from codemodder.codemods.secure_random import SecureRandom
from codemodder.codemods.url_sandbox import UrlSandbox


CODEMODS = {"secure-random": SecureRandom, "url-sandbox": UrlSandbox}


class IncludeExcludeConflict(Exception):
    def __init__(self):
        message = "Cannot pass both include and exclude flag"
        super().__init__(message)


def match_codemods(codemod_include: list, codemod_exclude: list):
    if not codemod_include and not codemod_exclude:
        return CODEMODS

    if codemod_include and codemod_exclude:
        raise IncludeExcludeConflict
    if codemod_exclude:
        to_exclude = set(codemod_exclude.split(","))
        return {
            name: codemod
            for (name, codemod) in CODEMODS.items()
            if name not in to_exclude
        }
    if codemod_include:
        to_includee = set(codemod_include.split(","))
        return {
            name: codemod for (name, codemod) in CODEMODS.items() if name in to_includee
        }
