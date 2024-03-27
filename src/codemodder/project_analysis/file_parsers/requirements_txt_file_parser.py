from pathlib import Path

import chardet

from codemodder.logging import logger
from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
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

        dependencies = self._clean_lines(lines)

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=dependencies,
            # requirements.txt files do not declare py versions explicitly
            # though we could create a heuristic by analyzing each dependency
            # and extracting py versions from them.
            py_versions=[],
        )

    def _clean_lines(self, lines: list[str]) -> set[str]:
        """Return a set of dependency `lines` excluding any lines
        that may be comments or may be pointers to other requirement files (-r ..._
        """
        return set(
            line.split("#")[0].strip()
            for line in lines
            if not line.startswith(("#", "-r "))
        )
