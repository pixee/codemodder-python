from pathlib import Path


def match_files(parent_path, exclude_paths=None):
    """

    :param parent_path: str name for starting directory
    :param exclude_paths: comma-separated set of UNIX glob patterns to exclude

    :return: list of <pathlib.PosixPath> files found within (including recursively) the parent directory
    that match the criteria of both exclude and include patterns.
    """
    exclude_patterns = exclude_paths.split(",") if exclude_paths else ""

    matching_files = []
    for file_path in Path(parent_path).rglob("*.py"):
        if any([file_path.match(exclude) for exclude in exclude_patterns]):
            # if a file matches any excluded pattern, do not include it
            continue
        matching_files.append(file_path)
    return matching_files
