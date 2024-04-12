import fnmatch
import itertools
from pathlib import Path
from typing import Optional, Sequence

DEFAULT_INCLUDED_PATHS = ["**.py", "**/*.py"]
DEFAULT_EXCLUDED_PATHS = [
    # TODO: test code should eventually only be excluded on a per-codemod basis
    # Some codemods represent fixes that should be applied to test code
    "test/**",
    "tests/**",
    "**/__test__/**",
    "**/__tests__/**",
    "conftest.py",
    "build/**",
    "dist/**",
    "venv/**",
    ".venv/**",
    ".tox/**",
    ".nox/**",
    ".eggs/**",
    ".git/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    ".hypothesis/**",
    ".coverage*",
]


def file_line_patterns(file_path: str | Path, patterns: Sequence[str]):
    """
    Find the lines included or excluded for a given file_path among the patterns
    """
    return [
        int(result[1])
        for pat in patterns
        if len(result := pat.split(":")) == 2
        and fnmatch.fnmatch(str(file_path), result[0])
    ]


def filter_files(names: Sequence[str], patterns: Sequence[str], exclude: bool = False):
    patterns = (
        [x.split(":")[0] for x in (patterns or [])]
        if not exclude
        # An excluded line should not cause the entire file to be excluded
        else [x for x in (patterns or []) if ":" not in x]
    )
    return itertools.chain(*[fnmatch.filter(names, pattern) for pattern in patterns])


def match_files(
    parent_path: str | Path,
    exclude_paths: Optional[Sequence[str]] = None,
    include_paths: Optional[Sequence[str]] = None,
):
    """
    Find pattern-matching files starting at the parent_path, recursively.

    If a file matches any exclude pattern, it is not matched. If any include
    patterns are passed in, a file must match `*.py` and at least one include patterns.

    :param parent_path: str name for starting directory
    :param exclude_paths: list of UNIX glob patterns to exclude
    :param include_paths: list of UNIX glob patterns to exclude

    :return: list of <pathlib.PosixPath> files found within (including recursively) the parent directory
    that match the criteria of both exclude and include patterns.
    """
    all_files = [
        str(Path(path).relative_to(parent_path))
        for path in Path(parent_path).rglob("*")
    ]
    included_files = set(
        filter_files(
            all_files,
            include_paths if include_paths is not None else DEFAULT_INCLUDED_PATHS,
        )
    )
    excluded_files = set(
        filter_files(
            all_files,
            exclude_paths if exclude_paths is not None else DEFAULT_EXCLUDED_PATHS,
            exclude=True,
        )
    )

    return [
        path
        for p in sorted(list(included_files - excluded_files))
        if (path := Path(parent_path).joinpath(p)).is_file()
    ]
