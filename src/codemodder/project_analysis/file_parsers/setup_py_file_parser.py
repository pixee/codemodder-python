from codemodder.project_analysis.file_parsers.package_store import PackageStore
from codemodder.utils.utils import clean_simplestring
from pathlib import Path
import libcst as cst
from libcst import matchers
from packaging.requirements import Requirement

from .base_parser import BaseParser


class SetupPyParser(BaseParser):
    @property
    def file_name(self):
        return "setup.py"

    def _parse_dependencies(self, dependencies):
        return [
            Requirement(line)
            for x in dependencies
            # Skip empty lines and comments
            if (line := clean_simplestring(x.value)) and not line.startswith("#")
        ]

    def _parse_dependencies_from_cst(self, cst_dependencies):
        # todo: handle cases for
        # 1. no dependencies,
        return self._parse_dependencies(cst_dependencies)

    def _parse_py_versions(self, version_str):
        # todo: handle for multiple versions
        return [clean_simplestring(version_str)]

    def _parse_file(self, file: Path):
        visitor = SetupCallVisitor()
        with open(str(file), "r", encoding="utf-8") as f:
            # todo: handle failure in parsing
            module = cst.parse_module(f.read())
        module.visit(visitor)

        # todo: handle no python_requires, install_requires

        return PackageStore(
            type=self.file_name,
            file=str(file),
            dependencies=self._parse_dependencies_from_cst(visitor.install_requires),
            py_versions=self._parse_py_versions(visitor.python_requires),
        )


class SetupCallVisitor(cst.CSTVisitor):
    def __init__(self):
        self.python_requires = None
        self.install_requires = None
        # todo setup_requires, tests_require, extras_require

    def visit_Call(self, node: cst.Call) -> None:
        # todo: only handle setup from setuptools, not others tho unlikely
        if matchers.matches(node.func, cst.Name(value="setup")):
            visitor = SetupArgVisitor()
            node.visit(visitor)
            self.python_requires = visitor.python_requires
            self.install_requires = visitor.install_requires


class SetupArgVisitor(cst.CSTVisitor):
    def __init__(self):
        self.python_requires = None
        self.install_requires = None

    def visit_Arg(self, node: cst.Arg) -> None:
        if matchers.matches(node.keyword, cst.Name(value="python_requires")):
            # todo: this works for `python_requires=">=3.7",` but what about
            # a list of versions?
            self.python_requires = node.value.value
        if matchers.matches(node.keyword, cst.Name(value="install_requires")):
            # todo: could it be something other than a list?
            self.install_requires = node.value.elements
