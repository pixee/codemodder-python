import django
from django.conf import settings
from django.db import models

# required to run this module standalone for testing
if not settings.configured:
    settings.configure()
django.setup()


class User(models.Model):
    name = models.CharField(max_length=100)
    phone = models.IntegerField(blank=True)
    class Meta:
        app_label = 'myapp'
