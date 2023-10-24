from codemodder.file_parsers import RequirementsTxtParser


class TestRequirementsTxtParser:
    def test_parse(self, dir_with_pkg_managers):
        parser = RequirementsTxtParser(dir_with_pkg_managers)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type == "requirements_txt"
        assert store.file == dir_with_pkg_managers / parser.file_name
        assert store.py_versions == []
        assert len(store.dependencies) == 4

    def test_parse_no_file(self, dir_with_pkg_managers):
        parser = RequirementsTxtParser(dir_with_pkg_managers / "foo")
        found = parser.parse()
        assert len(found) == 0
