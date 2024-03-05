from pathlib import Path

import pytest

from codemodder.code_directory import file_line_patterns, match_files


@pytest.fixture(scope="module")
def dir_structure(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    samples_dir = base_dir / "samples"
    samples_dir.mkdir()
    (samples_dir / "make_request.py").touch()
    (samples_dir / "insecure_random.py").touch()

    more_samples_dir = samples_dir / "more_samples"
    more_samples_dir.mkdir()
    (more_samples_dir / "empty_for_testing.py").touch()
    (more_samples_dir / "empty_for_testing.txt").touch()

    tests_dir = base_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_make_request.py").touch()
    (tests_dir / "test_insecure_random.py").touch()

    assert len(list(base_dir.rglob("*"))) == 9

    return base_dir


class TestMatchFiles:
    def _assert_expected(self, result_files, expected_files):
        assert len(result_files) == len(expected_files)
        file_names = [file.name for file in result_files]
        file_names.sort()
        assert file_names == expected_files

    def test_all_py_files_match(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files(dir_structure)
        self._assert_expected(files, expected)

    def test_match_excluded(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files(dir_structure, ["tests/**", "*request.py"])
        self._assert_expected(files, expected)

    def test_match_included_file_with_line(self, dir_structure):
        expected = ["insecure_random.py"]
        files = match_files(dir_structure, include_paths=["**/insecure_random.py:2"])
        self._assert_expected(files, expected)

    def test_match_excluded_line(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files(
            dir_structure, exclude_paths=["tests/**", "**/insecure_random.py:2"]
        )
        self._assert_expected(files, expected)

    def test_match_included_line_and_glob(self, dir_structure):
        expected = ["insecure_random.py"]
        files = match_files(dir_structure, include_paths=["**/insecure*.py:3"])
        self._assert_expected(files, expected)

    def test_match_excluded_line_and_glob(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files(
            dir_structure, exclude_paths=["tests/**", "**/insecure*.py:3"]
        )
        self._assert_expected(files, expected)

    def test_match_excluded_dir_incorrect_glob(self, dir_structure):
        incorrect_glob = "more_samples"
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files(dir_structure, ["tests/**", incorrect_glob])
        self._assert_expected(files, expected)

    def test_match_excluded_dir_correct_glob(self, dir_structure):
        correct_globs = ["**/more_samples/**", "*/more_samples/*"]
        for correct_glob in correct_globs:
            expected = ["insecure_random.py", "make_request.py"]
            files = match_files(dir_structure, ["tests/**", correct_glob])
            self._assert_expected(files, expected)

    def test_match_excluded_multiple(self, dir_structure):
        expected = ["insecure_random.py"]
        files = match_files(dir_structure, ["tests/**", "*request.py", "*empty*"])
        self._assert_expected(files, expected)

    def test_match_included(self, dir_structure):
        expected = ["make_request.py"]
        files = match_files(dir_structure, include_paths=["*request.py"])
        self._assert_expected(files, expected)

    def test_match_excluded_precedence_over_included(self, dir_structure):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files(
            dir_structure,
            exclude_paths=["tests/**", "*request.py"],
            include_paths=["*request.py", "*empty*.py", "*random.py"],
        )
        self._assert_expected(files, expected)

    def test_test_directory_not_excluded(self, dir_structure):
        expected = ["test_insecure_random.py", "test_make_request.py"]
        files = match_files(
            dir_structure, exclude_paths=["samples/**", "**/more_samples/**"]
        )
        self._assert_expected(files, expected)

    def test_include_test_overridden_by_default_excludes(self, mocker):
        mocker.patch(
            "codemodder.code_directory.Path.rglob",
            return_value=[
                "foo/tests/test_insecure_random.py",
                "foo/tests/test_make_request.py",
            ],
        )
        mocker.patch(
            "codemodder.code_directory.Path.is_file",
            return_value=True,
        )
        files = match_files(Path("."), include_paths=["tests/**"])
        self._assert_expected(files, [])

    def test_include_test_without_default_includes(self, mocker):
        files = ["foo/tests/test_insecure_random.py", "foo/tests/test_make_request.py"]
        mocker.patch(
            "codemodder.code_directory.Path.rglob",
            return_value=files,
        )
        mocker.patch(
            "codemodder.code_directory.Path.is_file",
            return_value=True,
        )
        result = match_files(Path("."), exclude_paths=[])
        assert result == [Path(x) for x in files]

    def test_extract_line_from_pattern(self):
        lines = file_line_patterns(Path("insecure_random.py"), ["insecure_*.py:3"])
        assert lines == [3]
