from core_codemods.django_receiver_on_top import DjangoReceiverOnTop
from core_codemods.sonar.api import SonarCodemod

SonarDjangoReceiverOnTop = SonarCodemod.from_core_codemod(
    name="django-receiver-on-top",
    other=DjangoReceiverOnTop,
    rule_id="python:S6552",
    rule_name="Django signal handler functions should have the `@receiver` decorator on top of all other decorators",
)
