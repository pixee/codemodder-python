from codemodder.codemods.base_codemod import Reference
from codemodder.codemods.sonar import SonarCodemod
from core_codemods.django_receiver_on_top import DjangoReceiverOnTop

SonarDjangoReceiverOnTop = SonarCodemod.from_core_codemod(
    name="django-receiver-on-top-S6552",
    other=DjangoReceiverOnTop,
    rules=["python:S6552"],
    new_references=[
        Reference(url="https://rules.sonarsource.com/python/type/Bug/RSPEC-6552/"),
    ],
)
