from dataclasses import dataclass

from packaging.requirements import Requirement


@dataclass
class License:
    name: str
    url: str


@dataclass
class Dependency:
    requirement: Requirement
    description: str
    _license: License
    oss_link: str
    package_link: str

    @property
    def name(self) -> str:
        return self.requirement.name

    @property
    def version(self) -> str:
        return self.requirement.specifier.__str__().strip()

    def build_description(self) -> str:
        return f"""{self.description}

License: [{self._license.name}]({self._license.url}) ✅ \
[Open Source]({self.oss_link}) ✅ \
[More facts]({self.package_link})
"""

    def __hash__(self):
        return hash(self.requirement)


FlaskWTF = Dependency(
    Requirement("flask-wtf~=1.2.0"),
    description="""\
            This package integrates WTForms into Flask. WTForms provides data validation and and CSRF protection which helps harden applications.
""",
    _license=License(
        "BSD-3-Clause",
        "https://opensource.org/license/BSD-3-clause/",
    ),
    oss_link="https://github.com/wtforms/flask-wtf/",
    package_link="https://pypi.org/project/Flask-WTF/",
)

DefusedXML = Dependency(
    Requirement("defusedxml~=0.7.1"),
    description="""\
This package is [recommended by the Python community](https://docs.python.org/3/library/xml.html#the-defusedxml-package) \
to protect against XML vulnerabilities.\
""",
    _license=License(
        "PSF-2.0",
        "https://opensource.org/license/python-2-0/",
    ),
    oss_link="https://github.com/tiran/defusedxml",
    package_link="https://pypi.org/project/defusedxml/",
)

Security = Dependency(
    Requirement("security~=1.2.0"),
    description="""This library holds security tools for protecting Python API calls.""",
    _license=License(
        "MIT",
        "https://opensource.org/license/MIT/",
    ),
    oss_link="https://github.com/pixee/python-security",
    package_link="https://pypi.org/project/security/",
)


DEPENDENCY_NOTIFICATION = """
## Dependency Updates

This codemod relies on an external dependency. We have automatically added this dependency to your project's `{filename}` file. 

{description} 

There are a number of places where Python project dependencies can be expressed, including `setup.py`, `pyproject.toml`, `setup.cfg`, and `requirements.txt` files. If this change is incorrect, or if you are using another packaging system such as `poetry`, it may be necessary for you to manually add the dependency to the proper location in your project.
"""

FAILED_DEPENDENCY_NOTIFICATION = """
## Dependency Updates

This codemod relies on an external dependency. However, we were unable to automatically add the dependency to your project. 

{description} 

There are a number of places where Python project dependencies can be expressed, including `setup.py`, `pyproject.toml`, `setup.cfg`, and `requirements.txt` files. You may need to manually add this dependency to the proper location in your project.

### Manual Installation

For `setup.py`:
```diff
 install_requires=[
+    "{requirement}",
 ],
```

For `pyproject.toml` (using `setuptools`):
```diff
 [project]
 dependencies = [
+    "{requirement}",
 ]
```

For `setup.cfg`:
```diff
 [options]
 install_requires =
+    {requirement}
```

For `requirements.txt`:
```diff
+{requirement}
```

For more information on adding dependencies to `setuptools` projects, see [the setuptools documentation](https://setuptools.pypa.io/en/latest/userguide/dependency_management.html#declaring-required-dependency). 

If you are using another build system, please refer to the documentation for that system to determine how to add dependencies.
"""


def build_dependency_notification(filename: str, dependency: Dependency) -> str:
    return DEPENDENCY_NOTIFICATION.format(
        filename=filename,
        description=dependency.description,
    )


def build_failed_dependency_notification(dependency: Dependency) -> str:
    return FAILED_DEPENDENCY_NOTIFICATION.format(
        description=dependency.description,
        requirement=dependency.requirement,
    )
