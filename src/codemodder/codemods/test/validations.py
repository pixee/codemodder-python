import importlib.util
import tempfile
from types import ModuleType
from typing import Optional


def execute_code(*, path=None, code=None, allowed_exceptions=None):
    """
    Ensure that code written in `path` or in `code` str is executable.
    """
    assert (path is None) != (
        code is None
    ), "Must pass either path to code or code as a str."

    if path:
        return _run_code(path, allowed_exceptions)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+t") as temp:
        temp.write(code)
        return _run_code(temp.name, allowed_exceptions)


def _run_code(path, allowed_exceptions=None) -> Optional[ModuleType]:
    """
    Execute the code in `path` in its own namespace.
    Return loaded module for any additional testing later on.
    """
    allowed_exceptions = allowed_exceptions or ()

    if not (spec := importlib.util.spec_from_file_location("output_code", path)):
        return None

    module = importlib.util.module_from_spec(spec)
    if not spec.loader:
        return None
    try:
        spec.loader.exec_module(module)
    except allowed_exceptions:
        pass

    return module
