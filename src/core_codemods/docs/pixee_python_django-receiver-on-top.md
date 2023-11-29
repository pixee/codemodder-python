Django uses signals to notify and handle actions that happens elsewhere in the application. You can define a response to a given signal by decorating a function with the `@receiver(signal)` decorator. The order in which the decorators are declared for this function is important. If the `@receiver` decorator is not on top, any decorators before it will be ignored. 
Our changes look something like this:

```diff
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from django.core.signals import request_finished

+@receiver(request_finished)
@csrf_exempt
-@receiver(request_finished)
def foo():
    pass
```
