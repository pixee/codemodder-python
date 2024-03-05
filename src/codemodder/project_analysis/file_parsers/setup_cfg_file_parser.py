import configparser
from pathlib import Path

from codemodder.logging import logger
from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
)

from .base_parser import BaseParser


class SetupCfgParser(BaseParser):
    @property
    def file_type(self):
        return FileType.SETUP_CFG

    def _parse_file(self, file: Path) -> PackageStore | None:
        config = configparser.ConfigParser()
        try:
            config.read(file)
        except configparser.ParsingError:
            logger.debug("Unable to parse setup.cfg file.")
            return None  # pragma: no cover

        if "options" not in config:
            return None

        dependency_lines = config["options"].get("install_requires", "").split("\n")
        python_requires = config["options"].get("python_requires", "")

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=set(line for line in dependency_lines if line),
            py_versions=[python_requires] if python_requires else [],
        )
