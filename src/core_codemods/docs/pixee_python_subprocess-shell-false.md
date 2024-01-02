This codemod sets the `shell` keyword argument to `False` in `subprocess` module function calls that have set it to `True`.

Setting `shell=True` will execute the provided command through the system shell which can lead to shell injection vulnerabilities. In the worst case this can give an attacker the ability to run arbitrary commands on your system. In most cases using `shell=False` is sufficient and leads to much safer code.

The changes from this codemod look like this:

```diff
 import subprocess
- subprocess.run("echo 'hi'", shell=True)
+ subprocess.run("echo 'hi'", shell=False)
```
