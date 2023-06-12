from codemodder.codemods.sarif_codemod import SarifCodemod
from pathlib import Path


class SemgrepCodemod(SarifCodemod):
    """
    A codemod that acts upon restults of a given YAML_FILE
    YAML_FILE: Path to a file that contains the semgrep rules it will act upon
    """

    YAML_FILE = Path()

    def __init__(self, results) -> None:
        super().__init__()
        self.results = results

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
