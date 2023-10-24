from codemodder.file_parsers.package_store import PackageStore
from pathlib import Path
import configparser

from .base_parser import BaseParser


class SetupCfgParser(BaseParser):
    def __init__(self, parent_directory: Path):
        super().__init__(parent_directory)
        self.file_name = "setup.cfg"

    def _parse_dependencies_from_toml(self, config: configparser.ConfigParser):
        # todo: handle cases for
        # 1. no dependencies, no options dict
        dependency_lines = config["options"]["install_requires"].split("\n")
        return self._parse_dependencies(dependency_lines)

    def _parse_py_versions(self, config: configparser.ConfigParser):
        # todo: handle cases for
        # 1. no options/ no requires-python
        # 2. various requires-python such as "">3.5.2"",  ">=3.11.1,<3.11.2"
        return config["options"]["python_requires"]

    def _parse_file(self, file: Path):
        config = configparser.ConfigParser()
        config.read(file)

        # todo: handle no config, no "options" in config

        return PackageStore(
            type=self.file_name,
            file=str(file),
            dependencies=self._parse_dependencies_from_toml(config),
            py_versions=self._parse_py_versions(config),
        )
