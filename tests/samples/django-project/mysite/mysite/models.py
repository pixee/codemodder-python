import django
from django.conf import settings
from django.db import models
# required to run this module standalone for testing
settings.configure()
django.setup()


class Message(models.Model):
    author = models.CharField(max_length=100)
    content = models.CharField(max_length=200)
    class Meta:
        app_label = 'myapp'
