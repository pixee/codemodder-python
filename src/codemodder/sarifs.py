import json
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from importlib.metadata import entry_points
from pathlib import Path
from typing import DefaultDict

from codemodder.logging import logger


class AbstractSarifToolDetector(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def detect(cls, run_data: dict) -> bool:
        pass


def detect_sarif_tools(filenames: list[Path]) -> DefaultDict[str, list[str]]:
    results: DefaultDict[str, list[str]] = defaultdict(list)

    logger.debug("loading registered SARIF tool detectors")
    detectors = {
        ent.name: ent.load() for ent in entry_points().select(group="sarif_detectors")
    }
    for fname in filenames:
        data = json.loads(fname.read_text())
        for name, det in detectors.items():
            # TODO: handle malformed sarif?
            for run in data["runs"]:
                try:
                    if det.detect(run):
                        logger.debug("detected %s sarif: %s", name, fname)
                        results[name].append(str(fname))
                except (KeyError, AttributeError, ValueError):
                    continue

    return results
