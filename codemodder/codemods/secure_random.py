import libcst as cst
from libcst import (
    FlattenSentinel,
    Module,
)
from libcst.codemod import (
    Codemod,
    CodemodContext,
)
from libcst.codemod.visitors import RemoveImportsVisitor
from typing import List
from codemodder.codemods.change import Change
from codemodder.codemods.base_codemod import (
    BaseCodemod,
    CodemodMetadata,
    ReviewGuidance,
)
from codemodder.codemods.base_visitor import BaseVisitor
from codemodder.file_context import FileContext


system_random_object_name = "gen"


class SecureRandom(BaseCodemod, Codemod):
    METADATA = CodemodMetadata(
        AUTHOR="dani.alcala@pixee.ai",
        DESCRIPTION="Replaces random.{func} with more secure secrets library functions.",
        NAME="secure-random",
        REVIEW_GUIDANCE=ReviewGuidance.MERGE_WITHOUT_REVIEW,
    )
    YAML_FILES = [
        "secure_random.yaml",
    ]

    def __init__(self, codemod_context: CodemodContext, file_context: FileContext):
        Codemod.__init__(self, codemod_context)
        BaseCodemod.__init__(self, file_context)

    def transform_module_impl(self, tree: Module) -> Module:
        # We first try to replace any random() call found by semgrep
        new_tree = RandomVisitor(
            self.context,
            self._results,
            self.file_context.line_exclude,
            self.file_context.line_include,
        ).transform_module(tree)
        # If any changes were made, we need to apply another transform, adding the import and gen object
        # TODO expensive, should probably use a boolean in the RandomVisitor
        if not new_tree.deep_equals(tree):
            SecureRandom.CHANGES_IN_FILE = RandomVisitor.CHANGES_IN_FILE
            new_tree = AddImportAndGen(self.context).transform_module(new_tree)
            new_tree = RemoveImportsVisitor(
                self.context, [("random", None, None)]
            ).transform_module(new_tree)
            return new_tree
        return tree


class AddImportAndGen(Codemod):
    def transform_module_impl(self, tree: Module) -> Module:
        first_statement = tree.children[0]
        new_import = cst.parse_statement("import secrets")
        add_gen = cst.parse_statement("gen = secrets.SystemRandom()")
        sentinel = FlattenSentinel((new_import, add_gen, first_statement))
        return tree.deep_replace(first_statement, sentinel)


class RandomVisitor(BaseVisitor):
    CHANGE_DESCRIPTION = "Switch use of requests for security.safe_requests"
    CHANGES_IN_FILE: List = []

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        pos_to_match = self.get_metadata(self.METADATA_DEPENDENCIES[0], original_node)
        if self.filter_by_result(
            pos_to_match
        ) and self.filter_by_path_includes_or_excludes(pos_to_match):
            line_number = pos_to_match.start.line
            self.CHANGES_IN_FILE.append(
                Change(str(line_number), self.CHANGE_DESCRIPTION).to_json()
            )
            return cst.parse_expression("gen.uniform(0, 1)")
        return updated_node
