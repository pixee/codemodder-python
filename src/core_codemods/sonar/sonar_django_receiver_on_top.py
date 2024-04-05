from core_codemods.django_receiver_on_top import DjangoReceiverOnTop
from core_codemods.sonar.api import SonarCodemod

SonarDjangoReceiverOnTop = SonarCodemod.from_core_codemod(
    name="django-receiver-on-top-S6552",
    other=DjangoReceiverOnTop,
    rule_id="python:S6552",
    rule_name="Django signal handler functions should have the `@receiver` decorator on top of all other decorators",
    rule_url="https://rules.sonarsource.com/python/type/Bug/RSPEC-6552/",
)
