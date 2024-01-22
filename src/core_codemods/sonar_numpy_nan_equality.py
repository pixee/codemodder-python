import libcst as cst
from codemodder.codemods.libcst_transformer import (
    LibcstTransformerPipeline,
)
from codemodder.codemods.sonar import SonarDetector
from codemodder.codemods.sonar import SonarCodemod

from core_codemods.api import Metadata
from core_codemods.numpy_nan_equality import (
    NumpyNanEquality,
    NumpyNanEqualityTransformer,
)


class SonarNumpyNanEqualityTransformer(NumpyNanEqualityTransformer):
    def leave_Comparison(
        self, original_node: cst.Comparison, updated_node: cst.Comparison
    ) -> cst.BaseExpression:
        if self.filter_by_result(self.node_position(original_node)):
            return super().leave_Comparison(original_node, updated_node)
        return updated_node


SonarNumpyNanEquality = SonarCodemod(
    metadata=Metadata(
        name="numpy-nan-equality-S6725",
        summary=NumpyNanEquality.summary,
        review_guidance=NumpyNanEquality._metadata.review_guidance,  # pylint: disable=protected-access
        references=NumpyNanEquality.references,
    ),
    transformer=LibcstTransformerPipeline(SonarNumpyNanEqualityTransformer),
    detector=SonarDetector(),
    requested_rules=["python:S6725"],
)
