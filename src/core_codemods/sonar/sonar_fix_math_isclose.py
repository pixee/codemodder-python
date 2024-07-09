import libcst as cst

from codemodder.codemods.libcst_transformer import LibcstTransformerPipeline
from codemodder.result import fuzzy_column_match, same_line
from core_codemods.fix_math_isclose import FixMathIsClose, FixMathIsCloseTransformer
from core_codemods.sonar.api import SonarCodemod


class FixMathIsCloseSonarTransformer(FixMathIsCloseTransformer):
    def filter_by_result(self, node) -> bool:
        """
        Special case result-matching for this rule because the sonar
        results returned match only the `math.isclose` call without `(...args...)`
        """
        match node:
            case cst.Call():
                pos_to_match = self.node_position(node)
                return any(
                    self.match_location(pos_to_match, result)
                    for result in self.results or []
                )
        return False

    def match_location(self, pos, result):
        return any(
            same_line(pos, location) and fuzzy_column_match(pos, location)
            for location in result.locations
        )


SonarFixMathIsClose = SonarCodemod.from_core_codemod(
    name="fix-math-isclose",
    other=FixMathIsClose,
    rule_id="python:S6727",
    rule_name="The abs_tol parameter should be provided when using math.isclose to compare values to 0",
    transformer=LibcstTransformerPipeline(FixMathIsCloseSonarTransformer),
)
