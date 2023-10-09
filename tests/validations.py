import importlib.util
import tempfile


def execute_code(*, path=None, code=None, allowed_exceptions=None):
    """
    Ensure that code written in `path` or in `code` str is executable.
    """
    assert (path is None) != (
        code is None
    ), "Must pass either path to code or code as a str."

    if path:
        _run_code(path, allowed_exceptions)
        return
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+t") as temp:
        temp.write(code)
        _run_code(temp.name, allowed_exceptions)


def _run_code(path, allowed_exceptions=None):
    """Execute the code in `path` in its own namespace."""
    allowed_exceptions = allowed_exceptions or ()

    spec = importlib.util.spec_from_file_location("output_code", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except allowed_exceptions:
        pass
