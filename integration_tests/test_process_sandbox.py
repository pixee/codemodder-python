from codemodder.codemods.test import BaseIntegrationTest
from codemodder.dependency import Security
from core_codemods.process_creation_sandbox import ProcessSandbox


class TestProcessSandbox(BaseIntegrationTest):
    codemod = ProcessSandbox
    original_code = """
    import subprocess

    subprocess.run("echo 'hi'", shell=True)
    subprocess.run(["ls", "-l"])
    
    subprocess.call("echo 'hi'", shell=True)
    subprocess.call(["ls", "-l"])
    
    subprocess.check_output(["ls", "-l"])
    
    var = "hello"
    """
    replacement_lines = [
        (2, """from security import safe_command\n\n"""),
        (3, """safe_command.run(subprocess.run, "echo 'hi'", shell=True)\n"""),
        (4, """safe_command.run(subprocess.run, ["ls", "-l"])\n"""),
        (6, """safe_command.run(subprocess.call, "echo 'hi'", shell=True)\n"""),
        (7, """safe_command.run(subprocess.call, ["ls", "-l"])\n"""),
    ]
    expected_diff = '--- \n+++ \n@@ -1,10 +1,11 @@\n import subprocess\n+from security import safe_command\n \n-subprocess.run("echo \'hi\'", shell=True)\n-subprocess.run(["ls", "-l"])\n+safe_command.run(subprocess.run, "echo \'hi\'", shell=True)\n+safe_command.run(subprocess.run, ["ls", "-l"])\n \n-subprocess.call("echo \'hi\'", shell=True)\n-subprocess.call(["ls", "-l"])\n+safe_command.run(subprocess.call, "echo \'hi\'", shell=True)\n+safe_command.run(subprocess.call, ["ls", "-l"])\n \n subprocess.check_output(["ls", "-l"])\n \n'
    expected_line_change = "3"
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
        (
            "# file used to test dependency management\n"
            "requests==2.31.0\n"
            "black==23.7.*\n"
            "mypy~=1.4\n"
            "pylint>1\n"
            f"{Security.requirement} \\\n"
        )
        + "\n".join(Security.build_hashes())
        + "\n"
    )