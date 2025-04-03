from abc import ABCMeta, abstractmethod
from collections import defaultdict
from importlib.metadata import entry_points
from pathlib import Path
from typing import DefaultDict

from pydantic import ValidationError
from sarif_pydantic import Run, Sarif

from codemodder.logging import logger


class AbstractSarifToolDetector(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def detect(cls, run_data: Run) -> bool:
        pass


def detect_sarif_tools(filenames: list[Path]) -> DefaultDict[str, list[Path]]:
    results: DefaultDict[str, list[Path]] = defaultdict(list)

    logger.debug("loading registered SARIF tool detectors")
    detectors = {
        ent.name: ent.load() for ent in entry_points().select(group="sarif_detectors")
    }
    for fname in filenames:
        try:
            data = Sarif.model_validate_json(fname.read_text(encoding="utf-8-sig"))
        except ValidationError:
            logger.exception("Invalid SARIF file: %s", fname)
            raise

        if not data.runs:
            raise ValueError(f"SARIF file without `runs` data: {fname}")

        for name, det in detectors.items():
            for run in data.runs:
                try:
                    if det.detect(run):
                        logger.debug("detected %s sarif: %s", name, fname)
                        results[name].append(Path(fname))
                except (KeyError, AttributeError, ValueError):
                    continue

    return results
