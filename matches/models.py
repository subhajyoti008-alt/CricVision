from django.core.exceptions import ValidationError
from django.db import models

from teams.models import Team
from tournaments.models import Tournament

# Create your models here.

class Match(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("LIVE", "Live"),
        ("COMPLETED", "Completed"),
        ("ABANDONED", "Abandoned"),
    ]

    STAGE_CHOICES = [
        ("LEAGUE", "League"),
        ("QUALIFIER_1", "Qualifier 1"),
        ("ELIMINATOR", "Eliminator"),
        ("QUALIFIER_2", "Oualifier 2"),
        ("FINAL", "Final"),
    ]

    tournament = models.ForeignKey(
        Tournament,
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name = "matches",   
    )

    home_team = models.ForeignKey(
        Team,
        on_delete = models.PROTECT,
        related_name = "home_matches",
    )

    away_team = models.ForeignKey(
        Team,
        on_delete = models.PROTECT,
        related_name = "away_matches",
    )

    venue = models.CharField(max_length=150, blank=True)
    scheduled_at = models.DateTimeField()
    over_per_innings = models.PositiveSmallIntegerField(default=6)

    status = models.CharField(
        max_length=12,
        choices = STATUS_CHOICES,
        default="SCHEDULED",
    )

    stage = models.CharField(
        max_length = 15,
        choices = STAGE_CHOICES,
        default = "LEAGUE"
    )

    toss_winner = models.ForeignKey(
        Team,
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "toss_wins"
    )

    toss_decision = models.CharField(
        max_length=4,
        choices = [
            ("BAT", "Bat"),
            ("BOWL", "Bowl"),
        ],
        blank = True,
    )

    winner = models.ForeignKey(
        Team,
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "match_wins",

    )
    result_summery = models.CharField(max_length=1000, blank=True)

    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["-scheduled_at"]

    def clean(self):
        if self.home_team == self.away_team:
            raise ValidationError(
                {"away_team": "A team cannot play against itself."}
            )
    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"
        