from django.contrib.auth.models import Permission
from django.db import models


class Plan(models.Model):
    """Its ``features`` are filled in a matrix: whether each is on and its limit."""

    name = models.CharField(max_length=100)
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """Its permissions are chosen in the permission matrix."""

    name = models.CharField(max_length=100)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name
