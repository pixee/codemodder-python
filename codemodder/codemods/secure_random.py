import libcst as cst
from libcst import (
    FlattenSentinel,
    Module,
    matchers,
)
from libcst.codemod import (
    Codemod,
    CodemodContext,
)
from libcst.codemod.visitors import RemoveImportsVisitor
from codemodder.codemods.base_codemod import BaseCodemod
from codemodder.codemods.base_visitor import BaseVisitor


system_random_object_name = "gen"


class SecureRandom(BaseCodemod, Codemod):
    NAME = "secure-random"
    DESCRIPTION = "Replaces random.{func} with more secure secrets library functions."
    AUTHOR = "dani.alcala@pixee.ai"
    YAML_FILES = [
        "secure-random.yaml",
    ]
    # TODO may be recovered by the yaml files themselves
    RULE_IDS = [
        "secure-random",
    ]

    def __init__(self, context: CodemodContext, results_by_id):
        Codemod.__init__(self, context)
        BaseCodemod.__init__(self, results_by_id)

    def transform_module_impl(self, tree: Module) -> Module:
        # We first try to replace any random() call found by semgrep
        new_tree = RandomVisitor(self.context, self._results).transform_module(tree)
        # If any changes were made, we need to apply another transform, adding the import and gen object
        # TODO expensive, should probably use a boolean in the RandomVisitor
        if not new_tree.deep_equals(tree):
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
    def __init__(self, context: CodemodContext, results):
        super().__init__(context, results)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if self.filter_by_result(original_node):
            # since it matched by position, this is a random call
            # TODO make this gather nodes only to change later
            return cst.parse_expression("gen.uniform(0, 1)")
            # return cst.Call(func=cst.Attribute(value=cst.Name(system_random_object_name),attr=cst.Name('uniform')),args=(cst.Arg(value=cst.Integer('0')),cst.Arg(value=cst.Integer('1'))))
        return updated_node
