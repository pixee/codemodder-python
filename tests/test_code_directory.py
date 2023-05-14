from codemodder.code_directory import match_files


class TestMatchFiles:
    def _assert_expected(self, result_files, expected_files):
        assert len(result_files) == len(expected_files)
        file_names = [file.name for file in result_files]
        file_names.sort()
        assert file_names == expected_files

    def test_all_files_match(self):
        expected = ["empty_for_testing.py", "insecure_random.py", "make_request.py"]
        files = match_files("tests/samples/")
        self._assert_expected(files, expected)

    def test_match_excluded(self):
        expected = ["empty_for_testing.py", "insecure_random.py"]
        files = match_files("tests/samples/", "*request.py")
        self._assert_expected(files, expected)
