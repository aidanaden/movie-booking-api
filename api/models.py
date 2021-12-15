from django.db import models
from django.utils import timezone
from django.db.models import JSONField

# Create your models here.
class Movie(models.Model):
    data = JSONField()

    def __str__(self) -> str:
        return f'{self.data}'

