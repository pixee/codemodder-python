import subprocess
import itertools
from tempfile import NamedTemporaryFile
from typing import List
from pathlib import Path
from codemodder.context import CodemodExecutionContext
from codemodder.sarifs import results_by_path_and_rule_id
from codemodder.logging import logger


def run(execution_context: CodemodExecutionContext, yaml_files: List[Path]) -> dict:
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

        if execution_context.path_exclude:
            command.extend(
                itertools.chain.from_iterable(
                    map(
                        lambda f: ["--exclude", f"{execution_context.directory}{f}"],
                        execution_context.path_exclude,
                    )
                )
            )
        if execution_context.path_include:
            # Note: parent path is not passed with --include
            command.extend(
                itertools.chain.from_iterable(
                    map(lambda f: ["--include", str(f)], execution_context.path_include)
                )
            )

        command.extend(
            itertools.chain.from_iterable(
                map(lambda f: ["--config", str(f)], yaml_files)
            )
        )
        command.append(str(execution_context.directory))
        logger.debug("semgrep command: `%s`", " ".join(command))
        subprocess.run(
            command,
            shell=False,
            check=True,
            stdout=None if execution_context.verbose else subprocess.PIPE,
            stderr=None if execution_context.verbose else subprocess.PIPE,
        )
        results = results_by_path_and_rule_id(temp_sarif_file.name)
        return results
