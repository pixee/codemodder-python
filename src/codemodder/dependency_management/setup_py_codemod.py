import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from codemodder.codemods.utils import is_setup_py_file
from codemodder.codemods.utils_mixin import NameResolutionMixin


class SetupPyAddDependencies(VisitorBasedCodemodCommand, NameResolutionMixin):
    def __init__(self, context: CodemodContext, dependencies):
        """
        :param dependencies:
        """
        super().__init__(context)
        self.filename = self.context.filename
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

        # todo: add self.dependencies to install_requires arg
        breakpoint()
        return updated_node


# filename = "tests/samples/pkg_w_setuppy/setup.py"
# with open(filename, "r", encoding="utf-8") as f:
#     source_tree = cst.parse_module(f.read())
#
# codemod = SetupPyAddDependencies(CodemodContext(filename=filename), ["dep1"])
# codemod.transform_module(source_tree)
