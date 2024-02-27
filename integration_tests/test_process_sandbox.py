from core_codemods.process_creation_sandbox import ProcessSandbox
from codemodder.codemods.test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)
from codemodder.dependency import Security


class TestProcessSandbox(BaseIntegrationTest):
    codemod = ProcessSandbox
    code_path = "tests/samples/make_process.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (1, """from security import safe_command\n\n"""),
            (2, """safe_command.run(subprocess.run, "echo 'hi'", shell=True)\n"""),
            (3, """safe_command.run(subprocess.run, ["ls", "-l"])\n"""),
            (5, """safe_command.run(subprocess.call, "echo 'hi'", shell=True)\n"""),
            (6, """safe_command.run(subprocess.call, ["ls", "-l"])\n"""),
        ],
    )
    expected_diff = '--- \n+++ \n@@ -1,10 +1,11 @@\n import subprocess\n+from security import safe_command\n \n-subprocess.run("echo \'hi\'", shell=True)\n-subprocess.run(["ls", "-l"])\n+safe_command.run(subprocess.run, "echo \'hi\'", shell=True)\n+safe_command.run(subprocess.run, ["ls", "-l"])\n \n-subprocess.call("echo \'hi\'", shell=True)\n-subprocess.call(["ls", "-l"])\n+safe_command.run(subprocess.call, "echo \'hi\'", shell=True)\n+safe_command.run(subprocess.call, ["ls", "-l"])\n \n subprocess.check_output(["ls", "-l"])\n \n'
    expected_line_change = "3"
    num_changes = 4
    num_changed_files = 2
    change_description = ProcessSandbox.change_description

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = (
        f"# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{Security.requirement} \\\n"
        f"{Security.build_hashes()}"
    )
