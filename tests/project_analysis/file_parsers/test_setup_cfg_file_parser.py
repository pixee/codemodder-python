import pytest

from codemodder.project_analysis.file_parsers import SetupCfgParser


@pytest.fixture(scope="module")
def pkg_with_setup_cfg(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("foo")
    setup_cfg = base_dir / "setup.cfg"
    cfg = """\
    [metadata]
    name = test pkg
    version = 123
    author = Some Name
    author_email = idk@gmail.com
    description = My package description
    license = BSD-3-Clause
    classifiers =
        Framework :: Django
        Programming Language :: Python :: 3

    [options]
    zip_safe = False
    include_package_data = True
    packages = find:
    python_requires = >=3.7
    install_requires =
        requests
        importlib-metadata; python_version<"3.8"
    """
    setup_cfg.write_text(cfg)
    return base_dir


class TestSetupCfgParser:
    def test_parse(self, pkg_with_setup_cfg):
        parser = SetupCfgParser(pkg_with_setup_cfg)
        found = parser.parse()
        assert len(found) == 1
        store = found[0]
        assert store.type.value == "setup.cfg"
        assert store.file == pkg_with_setup_cfg / parser.file_type.value
        assert store.py_versions == [">=3.7"]
        assert len(store.dependencies) == 2

    def test_parse_no_file(self, pkg_with_setup_cfg):
        parser = SetupCfgParser(pkg_with_setup_cfg / "foo")
        found = parser.parse()
        assert len(found) == 0

    def test_open_error(self, pkg_with_setup_cfg, mocker):
        mocker.patch("builtins.open", side_effect=Exception)
        parser = SetupCfgParser(pkg_with_setup_cfg)
        found = parser.parse()
        assert len(found) == 0

    def test_parser_error(self, pkg_with_setup_cfg, mocker):
        mocker.patch(
            "codemodder.project_analysis.file_parsers.setup_cfg_file_parser.configparser.ConfigParser.read",
            side_effect=Exception,
        )
        parser = SetupCfgParser(pkg_with_setup_cfg)
        found = parser.parse()
        assert len(found) == 0
