import subprocess
import itertools
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from codemodder.context import CodemodExecutionContext
from codemodder.sarifs import results_by_path_and_rule_id
from codemodder.logging import logger


def run_on_directory(yaml_files: List[Path], directory: Path):
    """
    Runs Semgrep and outputs a dict with the results organized by rule_id.
    """
    if not yaml_files:
        raise ValueError("No Semgrep rules were provided")

    with NamedTemporaryFile(prefix="semgrep", suffix=".sarif") as temp_sarif_file:
        command = [
            "semgrep",
            "scan",
            "--legacy",
            "--no-error",
            "--dataflow-traces",
            "--sarif",
            "-o",
            temp_sarif_file.name,
        ]
        command.extend(
            itertools.chain.from_iterable(
                map(lambda f: ["--config", str(f)], yaml_files)
            )
        )
        command.append(str(directory))
        logger.debug("semgrep command: `%s`", " ".join(command))
        # TODO: make sure to capture stderr and stdout in the event of a problem
        subprocess.run(
            command,
            shell=False,
            check=True,
            # TODO: report on verbose mode
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        results = results_by_path_and_rule_id(temp_sarif_file.name)
        return results


def run(execution_context: CodemodExecutionContext, yaml_files: List[Path]) -> dict:
    return run_on_directory(yaml_files, execution_context.directory)
