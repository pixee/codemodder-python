from codemodder.codemods.sonar import SonarCodemod
from core_codemods.fix_missing_self_or_cls import FixMissingSelfOrCls

SonarFixMissingSelfOrCls = SonarCodemod.from_core_codemod(
    name="fix-missing-self-or-cls-S5719",
    other=FixMissingSelfOrCls,
    rule_id="python:S5719",
    rule_name="Instance and class methods should have at least one positional parameter",
    rule_url="https://rules.sonarsource.com/python/RSPEC-5719/",
)
