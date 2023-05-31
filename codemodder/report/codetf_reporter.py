import json


class CodeTF:
    def __int__(self):
        self.report = {}

    def generate(self):
        pass

    def write_report(self, outfile):
        try:
            with open(outfile, "w", encoding="utf-8"):
                json.dump(self.report, outfile)
        except Exception:
            # Any issues with writing the output file should exit status 2.
            return 2
        return 0
