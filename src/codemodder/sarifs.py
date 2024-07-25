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


class DuplicateToolError(ValueError): ...


def detect_sarif_tools(filenames: list[Path]) -> DefaultDict[str, list[str]]:
    results: DefaultDict[str, list[str]] = defaultdict(list)

    logger.debug("loading registered SARIF tool detectors")
    detectors = {
        ent.name: ent.load() for ent in entry_points().select(group="sarif_detectors")
    }
    for fname in filenames:
        data = json.loads(fname.read_text(encoding="utf-8-sig"))
        for name, det in detectors.items():
            # TODO: handle malformed sarif?
            for run in data["runs"]:
                try:
                    if det.detect(run):
                        logger.debug("detected %s sarif: %s", name, fname)
                        # According to the Codemodder spec, it is invalid to have multiple SARIF results for the same tool
                        # https://github.com/pixee/codemodder-specs/pull/36
                        if name in results:
                            raise DuplicateToolError(
                                f"duplicate tool sarif detected: {name}"
                            )
                        results[name].append(str(fname))
                except DuplicateToolError as err:
                    raise err
                except (KeyError, AttributeError, ValueError):
                    continue

    return results
