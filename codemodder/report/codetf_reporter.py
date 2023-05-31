import json
from codemodder import __VERSION__
from codemodder.logging import logger


def base_report():
    return {
        "run": {
            "vendor": "pixee",
            "tool": "codemodder-python",
            "version": __VERSION__,
            "sarifs": [],
        },
        "results": {},
    }


class CodeTF:
    def __init__(self):
        self.report = base_report()
        # add version, command-line.. etc

    def generate(self, elapsed_ms, original_args, absolute_path):
        self.report["run"]["elapsed"] = str(elapsed_ms)
        self.report["run"]["commandLine"] = self._recreate_command(original_args)
        self.report["run"]["directory"] = absolute_path

    def _recreate_command(self, original_args):
        return f"python -m codemodder {' '.join(original_args)}"

    def write_report(self, outfile):
        try:
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(self.report, f)
        except Exception:
            logger.exception("Failed to write report file.")
            # Any issues with writing the output file should exit status 2.
            return 2
        logger.info("Wrote report to %s", outfile)
        return 0
