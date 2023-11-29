from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from django.core.signals import request_finished

@csrf_exempt
@receiver(request_finished)
def foo():
    pass
