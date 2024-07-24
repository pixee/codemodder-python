from codemodder.codemods.test import SonarIntegrationTest
from core_codemods.django_receiver_on_top import DjangoReceiverOnTopTransformer
from core_codemods.sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop


class TestDjangoReceiverOnTop(SonarIntegrationTest):
    codemod = SonarDjangoReceiverOnTop
    code_path = "tests/samples/django_receiver_on_top.py"
    replacement_lines = [
        (5, """@receiver(request_finished)\n"""),
        (6, """@csrf_exempt\n"""),
    ]
    # fmt: off
    expected_diff = (
    """--- \n"""
    """+++ \n"""
    """@@ -2,7 +2,7 @@\n"""
    """ from django.views.decorators.csrf import csrf_exempt\n"""
    """ from django.core.signals import request_finished\n"""
    """ \n"""
    """+@receiver(request_finished)\n"""
    """ @csrf_exempt\n"""
    """-@receiver(request_finished)\n"""
    """ def foo():\n"""
    """     pass\n"""
    )
    # fmt: on

    expected_line_change = "6"
    change_description = DjangoReceiverOnTopTransformer.change_description
    num_changed_files = 1
    num_changes = 2
