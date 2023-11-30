from typing import Optional
from codemodder.project_analysis.file_parsers.package_store import PackageStore
from pathlib import Path
from .base_parser import BaseParser
import chardet
from codemodder.logging import logger


class RequirementsTxtParser(BaseParser):
    @property
    def file_name(self):
        return "requirements.txt"

    def _parse_file(self, file: Path) -> Optional[PackageStore]:
        try:
            with open(file, "rb") as f:
                whole_file = f.read()
                enc = chardet.detect(f.read())
                lines = []
                if enc["confidence"] > 0.9:
                    encoding = enc.get("encoding")
                    decoded = whole_file.decode(encoding.lower()) if encoding else ""
                    lines = decoded.splitlines() if decoded else []
                else:
                    raise UnicodeError()
                return PackageStore(
                    type=self.file_name,
                    file=str(file),
                    dependencies=set(self._parse_dependencies(lines)),
                    # requirements.txt files do not declare py versions explicitly
                    # though we could create a heuristic by analyzing each dependency
                    # and extracting py versions from them.
                    py_versions=[],
                )
        except (UnicodeError, OSError):
            logger.debug("Error parsing file: %s", file)
        return None
