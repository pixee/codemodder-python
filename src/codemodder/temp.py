from django.db import models


class User(models.Model):
    name = models.CharField(max_length=100)
    phone = models.IntegerField(blank=True)

    def __str__(self):
        model_name = self.__class__.__name__
        fields_str = ", ".join((f"{field.name}={getattr(self, field.name)}" for field in self._meta.fields))
        return f"{model_name}({fields_str})"
