from django.db import models
from django.utils import timezone
from django.db.models import JSONField

# Create your models here.
class Movie(models.Model):
    slug = models.CharField(max_length=100, unique=True)
    data = JSONField()

    def __str__(self) -> str:
        return f'{self.data}'

