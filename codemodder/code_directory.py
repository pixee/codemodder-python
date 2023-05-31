from pathlib import Path


DEFAULT_INCLUDE = "*.py"


def py_file_matches(file_path, patterns):
    """
    file_path is suffixed with `.py` and matches at least one pattern.
    """
    is_py_file = file_path.match(DEFAULT_INCLUDE)
    if not patterns:
        return is_py_file
    return is_py_file and any(file_path.match(pattern) for pattern in patterns)


def match_files(parent_path, exclude_paths=None, include_paths=None):
    """
    Find pattern-matching files starting at the parent_path, recursively.

    If a file matches any exclude pattern, it is not matched. If any include
    patterns are passed in, a file must match `*.py` and at least one include patterns.

    :param parent_path: str name for starting directory
    :param exclude_paths: comma-separated set of UNIX glob patterns to exclude
    :param include_paths: comma-separated set of UNIX glob patterns to exclude

    :return: list of <pathlib.PosixPath> files found within (including recursively) the parent directory
    that match the criteria of both exclude and include patterns.
    """
    exclude_paths = list(exclude_paths) if exclude_paths is not None else []
    include_paths = list(include_paths) if include_paths is not None else []

    matched_files = []

    for file_path in Path(parent_path).rglob("*"):
        if file_path.is_file():
            # Exclude patterns take precedence over include patterns.
            if exclude_file(file_path, exclude_paths):
                continue

            if py_file_matches(file_path, include_paths):
                matched_files.append(file_path)

    return matched_files


def exclude_file(file_path, exclude_patterns):
    # if a file matches any excluded pattern, return True so it is not included for analysis
    return any(file_path.match(exclude) for exclude in exclude_patterns)
