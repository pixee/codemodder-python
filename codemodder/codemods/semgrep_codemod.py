from abc import abstractmethod
from codemodder.codemods.sarif_codemod import SarifCodemod
from pathlib import Path
from libcst.metadata import PositionProvider


class SemgrepCodemod(SarifCodemod):
    """
    A codemod that acts upon restults of a given YAML_FILE
    YAML_FILE: Path to a file that contains the semgrep rules it will act upon
    """

    METADATA_DEPENDENCIES = (PositionProvider,)

    YAML_FILE = Path()

    def __init__(self, results) -> None:
        super().__init__()
        self._results = results

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
