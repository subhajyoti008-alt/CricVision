from django.core.exceptions import ValidationError
from django.db import models

from teams.models import Team 

# Create your models here.

class Tournament(models.Model):
    FORMAT_CHOICES = [
        ("T10", "T10"),
        ("T20", "T20"),
        ("ODI", "One Day"), 
        ("CUSTOM", "Custom"),
    ]

    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=80)
    venue = models.CharField(max_length=150, blank=True)

    format = models.CharField(
        max_length = 10,
        choices = FORMAT_CHOICES,
        default = "T20",
    )
    over_per_innings = models.PositiveSmallIntegerField(default=20)
    
    start_date = models.DateField()
    end_date = models.DateField()

    teams = models.ManyToManyField(
        Team,
        blank=True,
        related_name = "tournaments",
    )

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["-start_date", "name"]

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": "End date cannot be before the start date."}
            )
        
    def __str__(self):
        return self.name