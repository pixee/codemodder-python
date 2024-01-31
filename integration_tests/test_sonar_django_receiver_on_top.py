from core_codemods.django_receiver_on_top import DjangoReceiverOnTopTransformer
from core_codemods.sonar.sonar_django_receiver_on_top import SonarDjangoReceiverOnTop
from integration_tests.base_test import (
    BaseIntegrationTest,
    original_and_expected_from_code_path,
)


class TestDjangoReceiverOnTop(BaseIntegrationTest):
    codemod = SonarDjangoReceiverOnTop
    code_path = "tests/samples/django_receiver_on_top.py"
    original_code, expected_new_code = original_and_expected_from_code_path(
        code_path,
        [
            (4, """@receiver(request_finished)\n"""),
            (5, """@csrf_exempt\n"""),
        ],
    )
    sonar_issues_json = "tests/samples/sonar_issues.json"

    # fmt: off
    expected_diff =(
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

    expected_line_change = "7"
    change_description = DjangoReceiverOnTopTransformer.change_description
    num_changed_files = 1
