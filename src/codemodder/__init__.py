try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    __version__ = "unknown"

from codemodder.codemodder import run

__all__ = ["run", "__version__"]
