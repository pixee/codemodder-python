from typing import Optional

import libcst as cst
from libcst import matchers
from libcst.codemod import CodemodContext
from packaging.requirements import Requirement

from codemodder.codemods.api import Metadata, ReviewGuidance, SimpleCodemod
from codemodder.codemods.utils import is_setup_py_file
from codemodder.codemods.utils_mixin import NameResolutionMixin
from codemodder.codetf import ChangeSet
from codemodder.dependency import Dependency
from codemodder.dependency_management.base_dependency_writer import DependencyWriter
from codemodder.diff import create_diff_from_tree
from codemodder.file_context import FileContext


def fixed_line_number_strategy(line_num_changed, _):
    return line_num_changed


class SetupPyWriter(DependencyWriter):
    def add_to_file(
        self, dependencies: list[Dependency], dry_run: bool = False
    ) -> Optional[ChangeSet]:
        input_tree = self._parse_file()
        wrapper = cst.MetadataWrapper(input_tree)
        file_context = FileContext(self.parent_directory, self.path, [], [], [])

        codemod = SetupPyAddDependencies(
            CodemodContext(wrapper=wrapper),
            file_context,
            dependencies=[dep.requirement for dep in dependencies],
            _transformer=True,
        )

        output_tree = codemod.transform_module(input_tree)
        if codemod.line_num_changed is None:
            return None

        diff = create_diff_from_tree(input_tree, output_tree)

        if not dry_run:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(output_tree.code)

        changes = self.build_changes(
            dependencies, fixed_line_number_strategy, codemod.line_num_changed
        )
        return ChangeSet(
            path=str(self.path.relative_to(self.parent_directory)),
            diff=diff,
            changes=changes,
        )

    def _parse_file(self):
        with open(self.path, encoding="utf-8") as f:
            return cst.parse_module(f.read())


class SetupPyAddDependencies(SimpleCodemod, NameResolutionMixin):
    metadata = Metadata(
        name="setup-py-add-dependencies",
        summary="Add Dependencies to `setup.py` `install_requires`",
        review_guidance=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )

    def __init__(
        self,
        codemod_context: CodemodContext,
        file_context: FileContext,
        dependencies: list[Requirement],
        **kwargs,
    ):
        SimpleCodemod.__init__(self, codemod_context, [], file_context, **kwargs)
        NameResolutionMixin.__init__(self)
        self.filename = self.file_context.file_path
        self.dependencies = dependencies
        self.line_num_changed = None

    def visit_Module(self, _: cst.Module) -> bool:
        """
        Only visit module with this codemod if it's a setup.py file.
        """
        return is_setup_py_file(self.filename)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if self.find_base_name(original_node.func) != "setuptools.setup":
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
        if not arg.value.elements:
            # If there are no current dependencies, don't do anything
            return arg

        # we add the new dependencies in the same line as the last
        # dependency listed in install_requires
        self.line_num_changed = self.lineno_for_node(arg.value.elements[-1]) - 1

        # grab the penultimate comma value if it has more than one element
        new_comma = cst.Comma(whitespace_after=cst.SimpleWhitespace(" "))
        last_element = arg.value.elements[-1]
        new_last_element = cst.Element(
            value=cst.SimpleString(value=f'"{str(self.dependencies[-1])}"')
        )
        if len(arg.value.elements) > 1:
            new_comma = arg.value.elements[-2].comma
            # if it has a newline, add a comma to the last element
            # this follows black's standard
            match new_comma.whitespace_after:
                case cst.ParenthesizedWhitespace(
                    first_line=cst.TrailingWhitespace(newline=cst.Newline())
                ):
                    new_last_element = new_last_element.with_changes(comma=cst.Comma())
        else:
            # infer the indentation from lbracket, if any
            match lbracket_whitespace := arg.value.lbracket.whitespace_after:
                case cst.ParenthesizedWhitespace():
                    new_comma = cst.Comma(
                        whitespace_after=cst.ParenthesizedWhitespace(
                            indent=True,
                            last_line=lbracket_whitespace.last_line,
                        )
                    )
                    # In a list with a single element, libcst will attribute the newline to the rbracket
                    match arg.value.rbracket.whitespace_before.first_line:
                        case cst.TrailingWhitespace(newline=cst.Newline()):
                            new_last_element = new_last_element.with_changes(
                                comma=cst.Comma()
                            )

        new_dependencies = [
            cst.Element(value=cst.SimpleString(value=f'"{str(dep)}"'), comma=new_comma)
            for dep in self.dependencies[:-1]
        ] + [new_last_element]

        return cst.Arg(
            keyword=arg.keyword,
            value=arg.value.with_changes(
                elements=[
                    *arg.value.elements[:-1],
                    last_element.with_changes(comma=new_comma),
                    *new_dependencies,
                ],
            ),
            equal=arg.equal,
            comma=arg.comma,
            star=arg.star,
            whitespace_after_star=arg.whitespace_after_star,
            whitespace_after_arg=arg.whitespace_after_arg,
        )
