from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

# Create your models here.
class Movie(models.Model):
    data = JSONField()

    def __str__(self) -> str:
        return f'{self.data}'

