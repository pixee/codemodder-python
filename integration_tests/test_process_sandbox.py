from codemodder.codemods.test.integration_utils import BaseRemediationIntegrationTest
from codemodder.dependency import Security
from core_codemods.process_creation_sandbox import ProcessSandbox


class TestProcessSandbox(BaseRemediationIntegrationTest):
    codemod = ProcessSandbox
    original_code = """
    import subprocess

    cmd = " ".join(["ls"])

    subprocess.run(cmd, shell=True)
    subprocess.run([cmd, "-l"])
    
    subprocess.call(cmd, shell=True)
    subprocess.call([cmd, "-l"])
    
    subprocess.check_output([cmd, "-l"])
    
    subprocess.run("ls -l", shell=True)

    var = "hello"
    """
    expected_diff_per_change = [
        '--- \n+++ \n@@ -1,8 +1,9 @@\n import subprocess\n+from security import safe_command\n \n cmd = " ".join(["ls"])\n \n-subprocess.run(cmd, shell=True)\n+safe_command.run(subprocess.run, cmd, shell=True)\n subprocess.run([cmd, "-l"])\n \n subprocess.call(cmd, shell=True)\n',
        '--- \n+++ \n@@ -1,9 +1,10 @@\n import subprocess\n+from security import safe_command\n \n cmd = " ".join(["ls"])\n \n subprocess.run(cmd, shell=True)\n-subprocess.run([cmd, "-l"])\n+safe_command.run(subprocess.run, [cmd, "-l"])\n \n subprocess.call(cmd, shell=True)\n subprocess.call([cmd, "-l"])\n',
        '--- \n+++ \n@@ -1,11 +1,12 @@\n import subprocess\n+from security import safe_command\n \n cmd = " ".join(["ls"])\n \n subprocess.run(cmd, shell=True)\n subprocess.run([cmd, "-l"])\n \n-subprocess.call(cmd, shell=True)\n+safe_command.run(subprocess.call, cmd, shell=True)\n subprocess.call([cmd, "-l"])\n \n subprocess.check_output([cmd, "-l"])\n',
        '--- \n+++ \n@@ -1,4 +1,5 @@\n import subprocess\n+from security import safe_command\n \n cmd = " ".join(["ls"])\n \n@@ -6,7 +7,7 @@\n subprocess.run([cmd, "-l"])\n \n subprocess.call(cmd, shell=True)\n-subprocess.call([cmd, "-l"])\n+safe_command.run(subprocess.call, [cmd, "-l"])\n \n subprocess.check_output([cmd, "-l"])\n \n',
    ]

    expected_lines_changed = [5, 6, 8, 9]
    num_changes = 4
    change_description = ProcessSandbox.change_description

    requirements_file_name = "requirements.txt"
    original_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
    )
    expected_requirements = (
        "# file used to test dependency management\n"
        "requests==2.31.0\n"
        "black==23.7.*\n"
        "mypy~=1.4\n"
        "pylint>1\n"
        f"{Security.requirement}\n"
    )
