import libcst as cst
from libcst.codemod import CodemodContext
from libcst import matchers
from codemodder.codemods.api import BaseCodemod
from codemodder.codemods.base_codemod import ReviewGuidance
from codemodder.codemods.utils import is_setup_py_file
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.file_context import FileContext
from packaging.requirements import Requirement


class SetupPyAddDependencies(BaseCodemod, NameResolutionMixin):
    NAME = "setup-py-add-dependencies"
    REVIEW_GUIDANCE = ReviewGuidance.MERGE_WITHOUT_REVIEW
    SUMMARY = "Add Dependencies to `setup.py` `install_requires`"
    DESCRIPTION = SUMMARY
    REFERENCES: list = []

    def __init__(
        self,
        codemod_context: CodemodContext,
        file_context: FileContext,
        dependencies: list[Requirement],
    ):
        BaseCodemod.__init__(self, codemod_context, file_context)
        NameResolutionMixin.__init__(self)
        self.filename = self.file_context.file_path
        self.dependencies = dependencies

    def visit_Module(self, _: cst.Module) -> bool:
        """
        Only visit module with this codemod if it's a setup.py file.
        """
        return is_setup_py_file(self.filename)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        true_name = self.find_base_name(original_node.func)
        if true_name != "setuptools.setup":
            return original_node

        new_args = self.replace_arg(original_node)
        return self.update_arg_target(updated_node, new_args)

    def replace_arg(self, original_node: cst.Call):
        new_args = []
        for arg in original_node.args:
            if matchers.matches(
                arg.keyword, matchers.Name("install_requires")
            ) and matchers.matches(arg.value, matchers.List()):
                new = self.add_dependencies_to_arg(arg)
            else:
                new = arg
            new_args.append(new)
        return new_args

    def add_dependencies_to_arg(self, arg: cst.Arg) -> cst.Arg:
        new_dependencies = [
            cst.Element(value=cst.SimpleString(value=f'"{str(dep)}"'))
            for dep in self.dependencies
        ]
        # TODO: detect if elements are separated by newline in source code.
        return cst.Arg(
            keyword=arg.keyword,
            value=arg.value.with_changes(
                elements=arg.value.elements + tuple(new_dependencies)
            ),
            equal=arg.equal,
            comma=arg.comma,
            star=arg.star,
            whitespace_after_star=arg.whitespace_after_star,
            whitespace_after_arg=arg.whitespace_after_arg,
        )
