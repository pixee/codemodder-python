from codemodder.project_analysis.file_parsers import RequirementsTxtParser


class TestRequirementsTxtParser:
    def test_parse(self, pkg_with_reqs_txt):
        parser = RequirementsTxtParser(pkg_with_reqs_txt)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type == "requirements.txt"
        assert store.file == str(pkg_with_reqs_txt / parser.file_name)
        assert store.py_versions == []
        assert len(store.dependencies) == 4

    def test_parse_no_file(self, pkg_with_reqs_txt):
        parser = RequirementsTxtParser(pkg_with_reqs_txt / "foo")
        found = parser.parse()
        assert len(found) == 0
