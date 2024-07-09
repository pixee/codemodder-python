from core_codemods.fix_missing_self_or_cls import FixMissingSelfOrCls
from core_codemods.sonar.api import SonarCodemod

SonarFixMissingSelfOrCls = SonarCodemod.from_core_codemod(
    name="fix-missing-self-or-cls",
    other=FixMissingSelfOrCls,
    rule_id="python:S5719",
    rule_name="Instance and class methods should have at least one positional parameter",
)
