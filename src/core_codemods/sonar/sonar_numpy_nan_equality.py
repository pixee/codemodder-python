from core_codemods.numpy_nan_equality import NumpyNanEquality
from core_codemods.sonar.api import SonarCodemod

SonarNumpyNanEquality = SonarCodemod.from_core_codemod(
    name="numpy-nan-equality-S6725",
    other=NumpyNanEquality,
    rule_id="python:S6725",
    rule_name="Equality checks should not be made against `numpy.nan`",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-6725/",
)
