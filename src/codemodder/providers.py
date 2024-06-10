from abc import ABCMeta, abstractmethod
from collections import UserDict
from importlib.metadata import entry_points

from codemodder.logging import logger


class BaseProvider(metaclass=ABCMeta):
    name: str
    _resource: str | None

    def __init__(self, name):
        self.name = name
        self._resource = self.load()

    @abstractmethod
    def load(self) -> str | None:
        pass

    @property
    def is_available(self) -> bool:
        return self.resource is not None

    @property
    def resource(self) -> str:
        if self._resource is None:
            raise ValueError(f"Resource for provider {self.name} is not available")
        return self._resource


class ProviderRegistry(UserDict):
    def add_provider(self, name: str, provider: BaseProvider):
        self[name] = provider

    def get_provider(self, name: str) -> BaseProvider | None:
        return self.get(name)


def load_providers() -> ProviderRegistry:
    registry = ProviderRegistry()
    logger.debug("loading registered providers")
    for entry_point in entry_points().select(group="codemod_providers"):
        logger.debug(
            '- loading provider "%s" from "%s"',
            entry_point.name,
            entry_point.module,
        )
        try:
            provider = entry_point.load()
        except Exception:
            logger.exception(
                'Failed to load provider "%s" from "%s": %s',
                entry_point.name,
                entry_point.module,
            )
            continue

        registry.add_provider(entry_point.name, provider(entry_point.name))

    return registry
