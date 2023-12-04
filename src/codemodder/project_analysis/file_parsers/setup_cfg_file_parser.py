from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)
from pathlib import Path
import configparser

from .base_parser import BaseParser


class SetupCfgParser(BaseParser):
    @property
    def file_type(self):
        return FileType.SETUP_CFG

    def _parse_file(self, file: Path) -> PackageStore | None:
        config = configparser.ConfigParser()
        config.read(file)

        if not (options := config["options"]):
            return None

        dependency_lines = options.get("install_requires", "").split("\n")
        python_requires = options.get("python_requires", "")

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=set(line for line in dependency_lines if line),
            py_versions=[python_requires] if python_requires else [],
        )
