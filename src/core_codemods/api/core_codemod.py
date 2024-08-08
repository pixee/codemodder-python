from codemodder.codemods.api import FindAndFixCodemod, RemediationCodemod
from codemodder.codemods.api import SimpleCodemod as _SimpleCodemod


class CoreCodemodDocsMixin:
    """
    Mixin for all codemods with docs provided by this package.
    """

    @property
    def docs_module_path(self):
        return "core_codemods.docs"


class CoreCodemod(CoreCodemodDocsMixin, FindAndFixCodemod):
    """
    Base class for all core codemods provided by this package.
    """

    @property
    def origin(self):
        return "pixee"


class SASTCodemod(CoreCodemodDocsMixin, RemediationCodemod):
    """
    Base class for all SAST codemods provided by this package.
    """


class SimpleCodemod(_SimpleCodemod):
    """
    Base class for all core codemods with a single detector and transformer.
    """

    codemod_base = CoreCodemod
