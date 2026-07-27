from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
class Innings(models.Model):
    match = models.ForeignKey(
        "matches.Match",
        on_delete = models.CASCADE,
        related_name = "innings", 
    )

    batting_team = models.ForeignKey(
        "teams.Team",
        on_delete = models.PROTECT,
        related_name = "batting_innings",
    )

    bowling_team = models.ForeignKey(
        "teams.Team",
        on_delete= models.PROTECT,
        related_name = "bowling_innings",
    )

    number = models.PositiveSmallIntegerField(
        help_text = "1 for the first innings, 2 for the second innings."
    )
    target_runs = models.PositiveSmallIntegerField(
        null = True,
        blank = True,
    )
    is_completed = models.BooleanField(default=False)

    opening_Striker = models.ForeignKey(
        "players.Player",
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "opened_as_striker",
    )

    opening_non_striker = models.ForeignKey(
        "players.Player",
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "opened_as_non_striker",
    )

    current_striker = models.ForeignKey(
        "players.Player",
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "currently_striking",
    )

    current_non_striker = models.ForeignKey(
        "players.Player",
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "currently_non_striking",
    )

    current_bowler = models.ForeignKey(
        "players.Player",
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "currently_bowling",
    )
    
    needs_new_bowler = models.BooleanField(default = False)

    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["match", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["match", "number"],
                name = "unique_innings_number_per_match",
            )
        ]
    
    @property
    def total_runs(self):
        totals = self.deliveries.aggregate(
            runs = Sum("runs_off_bat"),
            extras = Sum("extras"),
        )
        return (totals["runs"] or 0) + (totals["extras"] or 0)
    
    @property
    def wickets(self):
        return self.deliveries.filter(is_wicket=True).count()
    
    @property
    def legal_balls(self):
        return self.deliveries.filter(
            is_legal_delivery=True
        ).count()
    
    @property 
    def overs_display(self):
        overs, balls = divmod(self.legal_balls, 6)
        return f"{overs}.{balls}"
    
    @property
    def score_display(self):
        return f"{self.total_runs}/{self.wickets}"
    

    def clean(self):
        if self.batting_team_id == self.bowling_team_id:
            raise ValidationError(
                "Batting team and bowling team must be diffrent."
            )
        
    def __str__(self):
        return f"{self.match} - Innings {self.number}"
    

class Delivery(models.Model):
    EXTRA_TYPES = [
        ("NONE", "No extra"),
        ("WIDE", "Wide"),
        ("NO_BALL", "No ball"),
        ("BYE", "Bye"),
        ("LEG_BYE", "Leg bye"),
        ("PENALTY", "Penalty"),
    ]

    inning = models.ForeignKey(
        Innings,
        on_delete = models.CASCADE,
        related_name = "deliveries",
    )

    sequence = models.PositiveIntegerField(
        help_text = "Order of this delivery in the innings."
    )

    striker = models.ForeignKey(
        "players.Player",
        on_delete = models.PROTECT,
        related_name = "faced_deliveries",
    )
    non_striker = models.ForeignKey(
        "players.Player",
        on_delete = models.PROTECT,
        related_name = "non_striker_deliveries",
    )
    bowler = models.ForeignKey(
        "players.Player",
        on_delete = models.PROTECT,
        related_name = "bowled_deliveries",
    )

    runs_off_bat = models.PositiveSmallIntegerField(default=0)
    extras = models.PositiveSmallIntegerField(default=0)
    extra_type = models.CharField(
        max_length = 10,
        choices = EXTRA_TYPES,
        default = "NONE",
    )

    is_legal_delivery = models.BooleanField(default=True)

    is_wicket = models.BooleanField(default=False)
    wicket_player = models.ForeignKey(
        "players.Player",
        on_delete = models.PROTECT,
        null = True,
        blank = True,
        related_name = "dismissals",
    )
    dismissal_kind = models.CharField(max_length=50, blank= True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["inning", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields = ["inning", "sequence"],
                name = "unique_delivery_sequence_per_inning",
            )
        ]

    def clean(self):
        if self.extra_type in ["WIDE", "NO_BALL"] and self.is_legal_delivery:
            raise ValidationError(
                "Wides and no-balls are not legal deliveries."
            )
        
        if self.is_wicket and not self.wicket_player_id:
            raise ValidationError(
                {"wicket_player": "Select the dismissed player."}
            )
        
    def __str__(self):
        return f"{self.inning} - Delivery {self.sequence}"

