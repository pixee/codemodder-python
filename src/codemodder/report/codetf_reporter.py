import json
from os.path import abspath

from codemodder import __version__
from codemodder.logging import logger


def base_report():
    return {
        "run": {
            "vendor": "pixee",
            "tool": "codemodder-python",
            "version": __version__,
            "sarifs": [],
        },
        "results": [],
    }


def report_default(elapsed_ms, parsed_args, original_args, results_by_codemod):
    report = CodeTF()
    absolute_path = abspath(parsed_args.directory)
    report.generate(elapsed_ms, original_args, absolute_path, results_by_codemod)
    report.write_report(parsed_args.output)


class CodeTF:
    def __init__(self):
        self.report = base_report()

    def generate(self, elapsed_ms, original_args, absolute_path, results_by_codemod):
        self.report["run"]["elapsed"] = str(elapsed_ms)
        # TODO: this shouldn't be necessary, we should just use sys.argv
        # I think this is an artifact of using python -m codemodder, which is being deprecated
        self.report["run"]["commandLine"] = self._recreate_command(original_args)
        self.report["run"]["directory"] = absolute_path
        self.report["results"] = results_by_codemod

    def _recreate_command(self, original_args):
        return f"codemodder {' '.join(original_args)}"

    def write_report(self, outfile):
        try:
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(self.report, f)
        except Exception:
            logger.exception("failed to write report file.")
            # Any issues with writing the output file should exit status 2.
            return 2
        logger.debug("wrote report to %s", outfile)
        return 0
