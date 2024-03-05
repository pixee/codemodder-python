from pathlib import Path

import libcst as cst

from codemodder.project_analysis.file_parsers.package_store import (
    FileType,
    PackageStore,
)
from codemodder.utils.utils import clean_simplestring

from .base_parser import BaseParser


class SetupPyParser(BaseParser):
    @property
    def file_type(self):
        return FileType.SETUP_PY

    def _parse_file(self, file: Path) -> PackageStore | None:
        with open(file, "r", encoding="utf8") as f:
            module = cst.parse_module(f.read())

        visitor = SetupCallVisitor()
        module.visit(visitor)

        # todo: handle no python_requires, install_requires

        return PackageStore(
            type=self.file_type,
            file=file,
            dependencies=set(visitor.install_requires),
            py_versions=visitor.python_requires,
        )


class SetupCallVisitor(cst.CSTVisitor):
    python_requires: list[str]
    install_requires: list[str]

    def __init__(self):
        self.python_requires = []
        self.install_requires = []
        # TODO: setup_requires, tests_require, extras_require

    def visit_Call(self, node: cst.Call) -> None:
        # TODO: only handle setup from setuptools, not others tho unlikely
        match node.func:
            case cst.Name(value="setup"):
                visitor = SetupArgVisitor()
                node.visit(visitor)
                self.python_requires.extend(visitor.python_requires)
                self.install_requires.extend(visitor.install_requires)


class SetupArgVisitor(cst.CSTVisitor):
    python_requires: list[str]
    install_requires: list[str]

    def __init__(self):
        self.python_requires = []
        self.install_requires = []

    def visit_Arg(self, node: cst.Arg) -> None:
        match node.keyword, node.value:
            case cst.Name(value="python_requires"), cst.SimpleString() as string_node:
                # TODO: this works for `python_requires=">=3.7",` but what about a list of versions?
                self.python_requires.append(clean_simplestring(string_node.value))
            case cst.Name(value="install_requires"), cst.List() as list_node:
                for elm in list_node.elements:
                    match elm:
                        case cst.Element(value=cst.SimpleString() as string_node):
                            self.install_requires.append(
                                clean_simplestring(string_node.value)
                            )
