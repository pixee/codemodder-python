from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.fix_missing_self_or_cls import FixMissingSelfOrCls

SonarFixMissingSelfOrCls = SonarCodemod.from_core_codemod(
    name="fix-missing-self-or-cls-S5719",
    other=FixMissingSelfOrCls,
    rules=["python:S5719"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/RSPEC-5719/"),
    ],
)
