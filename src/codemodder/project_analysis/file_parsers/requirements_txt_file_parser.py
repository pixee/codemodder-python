from pathlib import Path

import chardet

from codemodder.logging import logger
from codemodder.project_analysis.file_parsers.package_store import (
    PackageStore,
    FileType,
)
from .base_parser import BaseParser


class RequirementsTxtParser(BaseParser):
    @property
    def file_type(self):
        return FileType.REQ_TXT

    def _parse_file(self, file: Path) -> PackageStore | None:
        with open(file, "rb") as f:
            whole_file = f.read()

        enc = chardet.detect(whole_file)
        if enc["confidence"] > 0.9:
            encoding = enc.get("encoding")
            decoded = whole_file.decode(encoding.lower()) if encoding else ""
            lines = decoded.splitlines() if decoded else []
        else:
            logger.debug("Unknown encoding for file: %s", file)
            return None

        dependencies = set(line.strip() for line in lines if not line.startswith("#"))

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=dependencies,
            # requirements.txt files do not declare py versions explicitly
            # though we could create a heuristic by analyzing each dependency
            # and extracting py versions from them.
            py_versions=[],
        )
