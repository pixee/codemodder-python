import fnmatch
from pathlib import Path


DEFAULT_INCLUDE = [
    "*.py",
]


def match_included(parent_path, globs):
    """
    Return a list of files within the parent_path that match
    all the globs plus DEFAULT_INCLUDE globs.
    """

    return matched_files


def match_files(parent_path, exclude_paths=None, include_paths=None):
    """
    Find pattern-matching files starting at the parent_path, recursively.

    If a file matches any exclude pattern, it is not matched. If any include
    patterns are passed in, a file must match ALL include patterns.

    :param parent_path: str name for starting directory
    :param exclude_paths: comma-separated set of UNIX glob patterns to exclude
    :param include_paths: comma-separated set of UNIX glob patterns to exclude

    :return: list of <pathlib.PosixPath> files found within (including recursively) the parent directory
    that match the criteria of both exclude and include patterns.
    """
    exclude_paths = list(exclude_paths) if exclude_paths is not None else []
    include_paths = list(include_paths) if include_paths is not None else []

    matched_files = []
    must_match_patterns = include_paths + DEFAULT_INCLUDE
    for file_path in Path(parent_path).rglob("*"):
        if file_path.is_file():
            # Exclude patterns take precedence over include patterns.
            if exclude_file(file_path, exclude_paths):
                continue

            if all(file_path.match(pattern) for pattern in must_match_patterns):
                matched_files.append(file_path)

    return matched_files


def exclude_file(file_path, exclude_patterns):
    # if a file matches any excluded pattern, return True so it is not included for analysis
    return any(file_path.match(exclude) for exclude in exclude_patterns)
