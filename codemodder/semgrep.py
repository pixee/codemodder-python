import json
import subprocess


def run():
    command = "semgrep scan tests/samples/ --config codemodder/codemods/semgrep  --sarif --output sarif.json --verbose"
    subprocess.run(command, shell=True, check=True)


def get_results():
    with open("sarif.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["runs"][0]["results"]
