from codemodder.codemods.test import BaseIntegrationTest
from codemodder.dependency import Security
from core_codemods.process_creation_sandbox import ProcessSandbox


class TestProcessSandbox(BaseIntegrationTest):
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
    replacement_lines = [
        (2, """from security import safe_command\n\n"""),
        (5, """safe_command.run(subprocess.run, cmd, shell=True)\n"""),
        (6, """safe_command.run(subprocess.run, [cmd, "-l"])\n"""),
        (8, """safe_command.run(subprocess.call, cmd, shell=True)\n"""),
        (9, """safe_command.run(subprocess.call, [cmd, "-l"])\n"""),
    ]
    expected_diff = '--- \n+++ \n@@ -1,12 +1,13 @@\n import subprocess\n+from security import safe_command\n \n cmd = " ".join(["ls"])\n \n-subprocess.run(cmd, shell=True)\n-subprocess.run([cmd, "-l"])\n+safe_command.run(subprocess.run, cmd, shell=True)\n+safe_command.run(subprocess.run, [cmd, "-l"])\n \n-subprocess.call(cmd, shell=True)\n-subprocess.call([cmd, "-l"])\n+safe_command.run(subprocess.call, cmd, shell=True)\n+safe_command.run(subprocess.call, [cmd, "-l"])\n \n subprocess.check_output([cmd, "-l"])\n \n'
    expected_line_change = "5"
    num_changes = 4
    num_changed_files = 2
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
