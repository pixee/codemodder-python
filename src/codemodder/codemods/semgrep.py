import io
import os
from pathlib import Path
import tempfile

import yaml

from codemodder.codemods.base_detector import BaseDetector
from codemodder.context import CodemodExecutionContext
from codemodder.result import ResultSet
from codemodder.semgrep import run as semgrep_run


def _populate_yaml(rule: str, codemod_id: str) -> str:
    rule_yaml = yaml.safe_load(io.StringIO(rule))
    config = {"rules": rule_yaml} if "rules" not in rule_yaml else rule_yaml
    config["rules"][0].setdefault("id", codemod_id)
    config["rules"][0].setdefault("message", "Semgrep found a match")
    config["rules"][0].setdefault("severity", "WARNING")
    config["rules"][0].setdefault("languages", ["python"])
    return yaml.safe_dump(config)


def _create_temp_yaml_file(rule: str, codemod_id: str):
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "w") as ff:
        ff.write(_populate_yaml(rule, codemod_id))

    return [Path(path)]


class SemgrepRuleDetector(BaseDetector):
    rule: str

    def __init__(self, rule: str):
        self.rule = rule

    def get_yaml_files(self, codemod_id: str) -> list[Path]:
        return _create_temp_yaml_file(self.rule, codemod_id)

    def apply(
        self,
        codemod_id: str,
        context: CodemodExecutionContext,
        files_to_analyze: list[Path],
    ) -> ResultSet:
        yaml_files = self.get_yaml_files(codemod_id)
        with context.timer.measure("semgrep"):
            return semgrep_run(context, yaml_files, files_to_analyze)
