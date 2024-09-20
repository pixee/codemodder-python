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
    "**/site-packages/**",
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


def filter_files(names: list[Path], patterns: Sequence[str], exclude: bool = False):
    patterns = (
        [x.split(":")[0] for x in (patterns or [])]
        if not exclude
        # An excluded line should not cause the entire file to be excluded
        else [x for x in (patterns or []) if ":" not in x]
    )
    return itertools.chain(
        *[fnmatch.filter((str(x) for x in names), pattern) for pattern in patterns]
    )


def files_for_directory(parent_path: Path) -> list[Path]:
    """
    Return list of all (non-symlink) file paths within a directory, recursively.
    """
    return [
        path
        for path in Path(parent_path).rglob("*")
        if Path(path).is_file() and not Path(path).is_symlink()
    ]


def match_files(
    parent_path: Path,
    input_paths: list[Path],
    exclude_paths: Optional[Sequence[str]] = None,
    include_paths: Optional[Sequence[str]] = None,
) -> list[Path]:
    """
    Find pattern-matching files starting at the parent_path, recursively.

    If a file matches any exclude pattern, it is not matched. If any include
    patterns are passed in, a file must match at least one include patterns.

    :param parent_path: str name for starting directory
    :param exclude_paths: list of UNIX glob patterns to exclude, uses DEFAULT_EXCLUDED_PATHS if None
    :param include_paths: list of UNIX glob patterns to exclude, uses DEFAULT_INCLUDED_PATHS if None

    :return: list of <pathlib.PosixPath> files found within (including recursively) the parent directory
    that match the criteria of both exclude and include patterns.
    """
    paths = [p.relative_to(parent_path) for p in input_paths]
    included_files = set(
        filter_files(
            paths,
            include_paths if include_paths is not None else DEFAULT_INCLUDED_PATHS,
        )
    )
    excluded_files = set(
        filter_files(
            paths,
            exclude_paths if exclude_paths is not None else DEFAULT_EXCLUDED_PATHS,
            exclude=True,
        )
    )

    return [
        parent_path.joinpath(p) for p in sorted(list(included_files - excluded_files))
    ]
