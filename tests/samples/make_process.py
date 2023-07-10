import subprocess

subprocess.run("echo 'hi'", shell=True)
subprocess.run(["ls", "-l"])

subprocess.call("echo 'hi'", shell=True)
subprocess.call(["ls", "-l"])

subprocess.check_output(["ls", "-l"])

var = "hello"
