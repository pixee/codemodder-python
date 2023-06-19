from typing import Union
import libcst as cst
from libcst import (
    BaseStatement,
    CSTTransformer,
    FlattenSentinel,
    Module,
    RemovalSentinel,
    SimpleStatementLine,
    matchers,
)
from libcst.codemod import (
    Codemod,
    CodemodContext,
    ContextAwareTransformer,
    VisitorBasedCodemodCommand,
)
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import PositionProvider
from codemodder.codemods.base_codemod import BaseCodemod
import itertools

system_random_object_name = "gen"


class SecureRandom(BaseCodemod, Codemod):
    METADATA_DEPENDENCIES = (PositionProvider,)

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

    # TODO we need to filter files by results
    def __init__(self, context: CodemodContext, results_by_id):
        super().__init__(context)
        self.__results = list(
            itertools.chain.from_iterable(
                map(lambda rId: results_by_id[rId], self.RULE_IDS)
            )
        )

    def transform_module_impl(self, tree: Module) -> Module:
        # We first try to replace any random() call found by semgrep
        new_tree = SecureRandomVisitor(self.context, self.__results).transform_module(
            tree
        )
        # If any changes were made, we need to apply another transform, adding the import and gen object
        # TODO expensive, should probably use a boolean in the SecureRandomVisitor
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


class SecureRandomVisitor(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, context: CodemodContext, results):
        super(VisitorBasedCodemodCommand, self).__init__(context)
        self.added_gen_and_import = False
        self.__results = results

    @property
    def results(self):
        return self.__results

    def filter_by_result(self, node):
        pos_to_match = self.get_metadata(PositionProvider, node)
        all_pos = [extract_pos_from_result(result) for result in self.results]
        return any(match_pos(pos_to_match, position) for position in all_pos)

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):
        if self.filter_by_result(original_node):
            # since it matched by position, this is a random call
            # TODO make this gather nodes only to change later
            return cst.parse_expression("gen.uniform(0,1)")
            # return cst.Call(func=cst.Attribute(value=cst.Name(system_random_object_name),attr=cst.Name('uniform')),args=(cst.Arg(value=cst.Integer('0')),cst.Arg(value=cst.Integer('1'))))
        return updated_node


def match_pos(pos, x):
    # needs some leeway because the semgrep and libcst won't exactly match
    return (
        pos.start.line == x[0]
        and (pos.start.column in (x[1] - 1, x[1]))
        and pos.end.line == x[2]
        and (pos.end.column in (x[3] - 1, x[3]))
    )


def extract_pos_from_result(result):
    region = result["locations"][0]["physicalLocation"]["region"]
    # TODO it may be the case some of these attributes do not exist
    return (
        region.get("startLine"),
        region["startColumn"],
        region.get("endLine") or region.get("startLine"),
        region["endColumn"],
    )


def is_random_call(node: cst.Call) -> bool:
    """
    Matches x.random() or random()
    """
    is_random = matchers.Call(
        func=matchers.Attribute(
            value=matchers.DoNotCare(), attr=matchers.Name(value="random")
        )
    )
    return matchers.matches(node, is_random)


def is_randint_node(node: cst.Expr) -> bool:
    """
    Check to see if either: random.randint() or randint() is called.

    :param node:
    :return: bool
    """

    library_dot_randint = matchers.Expr(
        value=matchers.Call(
            func=matchers.Attribute(
                value=matchers.Name(value="random"), attr=matchers.Name(value="randint")
            )
        )
    )
    direct_randint = matchers.Expr(
        value=matchers.Call(func=matchers.Name(value="randint"))
    )

    return matchers.matches(
        node,
        matchers.OneOf(library_dot_randint, direct_randint),
    )


def is_random_import(node: cst.Import | cst.ImportFrom) -> bool:
    import_alias_random = matchers.ImportAlias(name=matchers.Name(value="random"))
    import_alias_randint = matchers.ImportAlias(name=matchers.Name(value="randint"))
    direct_import = matchers.Import(names=[import_alias_random])
    from_random_import_random = matchers.ImportFrom(
        module=cst.Name(value="random"), names=[import_alias_random]
    )
    from_random_import_randint = matchers.ImportFrom(
        module=cst.Name(value="random"), names=[import_alias_randint]
    )

    return matchers.matches(
        node,
        matchers.OneOf(
            direct_import, from_random_import_random, from_random_import_randint
        ),
    )
