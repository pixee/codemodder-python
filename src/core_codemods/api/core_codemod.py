from codemodder.codemods.api import BaseCodemod, SimpleCodemod as _SimpleCodemod


class CoreCodemod(BaseCodemod):
    """
    Base class for all core codemods provided by this package.
    """

    @property
    def origin(self):
        return "pixee"

    @property
    def docs_module_path(self):
        return "core_codemods.docs"


class SimpleCodemod(_SimpleCodemod):
    """
    Base class for all core codemods with a single detector and transformer.
    """

    codemod_base = CoreCodemod
