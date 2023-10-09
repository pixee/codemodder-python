import importlib.util
import tempfile

def validate_code(*, path=None, code=None):
    """
    Ensure that code written in `path` or in `code` str is importable.
    """
    assert (path is None) != (code is None), "Must pass either path to code or code as a str."

    if path:
        _try_code_import(path)
        return
    with tempfile.NamedTemporaryFile(suffix=".py", mode='w+t') as temp:
        temp.write(code)
        _try_code_import(temp.name)

def _try_code_import(path):
    spec = importlib.util.spec_from_file_location("output_code", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
