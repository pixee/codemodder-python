from codemodder.project_analysis.file_parsers import RequirementsTxtParser


class TestRequirementsTxtParser:
    def test_parse(self, pkg_with_reqs_txt):
        parser = RequirementsTxtParser(pkg_with_reqs_txt)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "requirements.txt"
        assert store.file == pkg_with_reqs_txt / parser.file_type.value
        assert store.py_versions == []
        assert len(store.dependencies) == 4

    def test_parse_utf_16(self, pkg_with_reqs_txt_utf_16):
        parser = RequirementsTxtParser(pkg_with_reqs_txt_utf_16)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "requirements.txt"
        assert store.file == pkg_with_reqs_txt_utf_16 / parser.file_type.value
        assert store.py_versions == []
        assert len(store.dependencies) == 4

    def test_parse_unknown_encoding(self, pkg_with_reqs_txt_unknown_encoding):
        parser = RequirementsTxtParser(pkg_with_reqs_txt_unknown_encoding)
        found = parser.parse()
        assert len(found) == 0

    def test_parse_no_file(self, pkg_with_reqs_txt):
        parser = RequirementsTxtParser(pkg_with_reqs_txt / "foo")
        found = parser.parse()
        assert len(found) == 0

    def test_open_error(self, pkg_with_reqs_txt, mocker):
        mocker.patch("builtins.open", side_effect=Exception)
        parser = RequirementsTxtParser(pkg_with_reqs_txt)
        found = parser.parse()
        assert len(found) == 0

    def test_trailing_comments(self, pkg_with_reqs_txt_and_comments):
        parser = RequirementsTxtParser(pkg_with_reqs_txt_and_comments)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "requirements.txt"
        assert store.file == pkg_with_reqs_txt_and_comments / parser.file_type.value
        assert store.py_versions == []
        assert len(store.dependencies) == 4

    def test_parse_with_r_line(self, pkg_with_reqs_r_line):
        parser = RequirementsTxtParser(pkg_with_reqs_r_line)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "requirements.txt"
        assert store.file == pkg_with_reqs_r_line / parser.file_type.value
        assert store.py_versions == []
        assert len(store.dependencies) == 4
