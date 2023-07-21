from codemodder.codemods.process_creation_sandbox import ProcessSandbox
from integration_tests.base_test import BaseIntegrationTest


class TestProcessSandbox(BaseIntegrationTest):
    codemod = ProcessSandbox
    code_path = "tests/samples/make_process.py"
    original_code = 'import subprocess\n\nsubprocess.run("echo \'hi\'", shell=True)\nsubprocess.run(["ls", "-l"])\n\nsubprocess.call("echo \'hi\'", shell=True)\nsubprocess.call(["ls", "-l"])\n\nsubprocess.check_output(["ls", "-l"])\n\nvar = "hello"\n'
    expected_new_code = 'import subprocess\nfrom security import safe_command\n\nsafe_command.run(subprocess.run, "echo \'hi\'", shell=True)\nsafe_command.run(subprocess.run, ["ls", "-l"])\n\nsafe_command.call(subprocess.call, "echo \'hi\'", shell=True)\nsafe_command.call(subprocess.call, ["ls", "-l"])\n\nsubprocess.check_output(["ls", "-l"])\n\nvar = "hello"\n'
    expected_diff = '--- \n+++ \n@@ -1,10 +1,11 @@\n import subprocess\n+from security import safe_command\n \n-subprocess.run("echo \'hi\'", shell=True)\n-subprocess.run(["ls", "-l"])\n+safe_command.run(subprocess.run, "echo \'hi\'", shell=True)\n+safe_command.run(subprocess.run, ["ls", "-l"])\n \n-subprocess.call("echo \'hi\'", shell=True)\n-subprocess.call(["ls", "-l"])\n+safe_command.call(subprocess.call, "echo \'hi\'", shell=True)\n+safe_command.call(subprocess.call, ["ls", "-l"])\n \n subprocess.check_output(["ls", "-l"])\n \n'
    expected_line_change = "3"
    num_changes = 4
    change_description = ProcessSandbox.CHANGE_DESCRIPTION

    requirements_path = "tests/samples/requirements.txt"
    original_requirements = "# file used to test dependency management\nrequests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\n"
    expected_new_reqs = (
        "requests==2.31.0\nblack==23.7.*\nmypy~=1.4\npylint>1\nsecurity==1.0.1"
    )
