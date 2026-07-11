from django.db import models

from players.models import Player

# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=120, unique=True)
    short_name = models.CharField(max_length=5, unique=True)
    city = models.CharField(max_length
    
    =80, blank=True)

    captain = models.ForeignKey(
        Player,
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "captained_teams",
    )

    players = models.ManyToManyField(
        Player,
        blank=True,
        related_name = "teams",
    )

    created_at = models.DateTimeField(auto_now_add =True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name 