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
