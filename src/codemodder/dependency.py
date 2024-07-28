from dataclasses import dataclass, field

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
    hashes: list[str] = field(default_factory=list)
    # Forward reference
    type_stubs: list["Dependency"] = field(default_factory=list)

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

    def build_hashes(self) -> list[str]:
        return [f"{' '*4}--hash=sha256:{sha256}" for sha256 in self.hashes]

    def __hash__(self):
        return hash(self.requirement)


FlaskWTF = Dependency(
    Requirement("flask-wtf==1.2.1"),
    hashes=[
        "fa6793f2fb7e812e0fe9743b282118e581fb1b6c45d414b8af05e659bd653287",
        "8bb269eb9bb46b87e7c8233d7e7debdf1f8b74bf90cc1789988c29b37a97b695",
    ],
    description="""\
            This package integrates WTForms into Flask. WTForms provides data validation and and CSRF protection which helps harden applications.
""",
    _license=License(
        "BSD-3-Clause",
        "https://opensource.org/license/BSD-3-clause/",
    ),
    oss_link="https://github.com/wtforms/flask-wtf/",
    package_link="https://pypi.org/project/Flask-WTF/",
    type_stubs=[
        Dependency(
            Requirement("types-WTForms==3.1.0.20240425"),
            hashes=[
                "449b6e3756b2bc70657e98d989bdbf572a25466428774be96facf9debcbf6c4e",
                "49ffc1fe5576ea0735b763fff77e7060dd39ecc661276cbd0b47099921b3a6f2",
            ],
            description="""\
                    This is a type stub package for the WTForms package.
        """,
            _license=License(
                "Apache-2.0",
                "https://opensource.org/license/apache-2-0",
            ),
            oss_link="https://github.com/python/typeshed",
            package_link="https://pypi.org/project/types-WTForms/",
        ),
    ],
)

DefusedXML = Dependency(
    Requirement("defusedxml==0.7.1"),
    hashes=[
        "a352e7e428770286cc899e2542b6cdaedb2b4953ff269a210103ec58f6198a61",
        "1bb3032db185915b62d7c6209c5a8792be6a32ab2fedacc84e01b52c51aa3e69",
    ],
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
    type_stubs=[
        Dependency(
            Requirement("types-defusedxml==0.7.0.20240218"),
            hashes=[
                "2b7f3c5ca14fdbe728fab0b846f5f7eb98c4bd4fd2b83d25f79e923caa790ced",
                "05688a7724dc66ea74c4af5ca0efc554a150c329cb28c13a64902cab878d06ed",
            ],
            description="""\
                This is a type stub package for the defusedxml package.
    """,
            _license=License(
                "Apache-2.0",
                "https://opensource.org/license/apache-2-0",
            ),
            oss_link="https://github.com/python/typeshed",
            package_link="https://pypi.org/project/types-defusedxml/",
        ),
    ],
)

Security = Dependency(
    Requirement("security==1.3.1"),
    hashes=[
        "9df6e75393f494ca3fd06dac3ed02f3c4fed60842b13fd00757b026cedff426b",
        "7ec0853c74c7dd22a9967bda087db5d4a7df58253574e60ec475c660f839da6d",
    ],
    description="""This library holds security tools for protecting Python API calls.""",
    _license=License(
        "MIT",
        "https://opensource.org/license/MIT/",
    ),
    oss_link="https://github.com/pixee/python-security",
    package_link="https://pypi.org/project/security/",
)

Fickling = Dependency(
    Requirement("fickling~=0.1.0,>=0.1.3"),
    hashes=[
        "c7ad5885cd97f8c693cf7824fdbcf9d103dbacbce36546e5a031805a7261bb74",
        "606b3153ad4b2c0338930d08a739f7f10a560f996e0bd3a4b46544417254b0d0",
    ],
    description="""This package provides analysis of pickled data to help identify potential security vulnerabilities.""",
    _license=License(
        "LGPL-3.0",
        "https://opensource.org/license/LGPL-3.0/",
    ),
    oss_link="https://github.com/trailofbits/fickling",
    package_link="https://pypi.org/project/fickling/",
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
