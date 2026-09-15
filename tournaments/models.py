from django.core.exceptions import ValidationError
from django.db import models
from teams.models import Team 
from players.models import Player
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Tournament(models.Model):
    FORMAT_CHOICES = [
        ("T10", "T10"),
        ("T20", "T20"),
        ("ODI", "One Day"), 
        ("CUSTOM", "Custom"),
    ]

    COMPETITION_TYPES = [
        ("NORMAL", "Normal Tournament"),
        ("PREMIER_LEAGUE", "Premier League"),
    ]

    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=80)
    venue = models.CharField(max_length=150, blank=True)

    format = models.CharField(
        max_length = 10,
        choices = FORMAT_CHOICES,
        default = "T20",
    )

    competition_type = models.CharField(
        max_length = 20,
        choices = COMPETITION_TYPES,
        default = "NORMAL",
    )

    over_per_innings = models.PositiveSmallIntegerField(default=6)
    entry_fee = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0,
)

    
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


class Registration(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("UNPAID", "Unpaid"),
        ("PENDING", "Penduing"),
        ("PAID", "Paid"),
        ("WAIVED", "Fee waived"),
    ]

    player = models.ForeignKey(
        Player,
        on_delete = models.CASCADE,
        related_name = "registrations",
    )

    tournament = models.ForeignKey(
        Tournament,
        on_delete = models.CASCADE,
        related_name = "registrations"
    )

    status = models.CharField(
        max_length = 10,
        choices = STATUS_CHOICES,
        default = "PENDING",
    )

    payment_status = models.CharField(
        max_length = 10,
        choices = PAYMENT_STATUS_CHOICES,
        default = "UNPAID",
    )

    created_at = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields = ["player", "tournament"],
                name = "unique_player_registration_per_tournament",
            )
        ]

        def __str__(self):
            return f"{self.player} - {self.tournament}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
        ("WAIVED", "Fee waived"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending verification"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    ]

    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="payment",
    )

    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    transaction_reference = models.CharField(
        max_length=150,
        blank=True,
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.registration} - {self.get_status_display()}"

    def verify(self, organizer):
        self.status = "VERIFIED"
        self.verified_by = organizer
        self.verified_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status == "VERIFIED":
            if self.method == "WAIVED":
                self.registration.payment_status = "WAIVED"
            else:
                self.registration.payment_status = "PAID"
        elif self.status == "PENDING":
            self.registration.payment_status = "PENDING"
        else:
            self.registration.payment_status = "UNPAID"

        self.registration.save(update_fields=["payment_status"])


class Auction(models.Model):
    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("SOLD", "Sold"),
        ("UNSOLD", "Unsold"),
    ]

    registration = models.OneToOneField(
        Registration,
        on_delete=models.CASCADE,
        related_name="auction",
    )

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    current_bid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="AVAILABLE",
    )

    winning_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="won_auctions",
    )

    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    listed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["status", "registration__player__full_name"]

    def __str__(self):
        return f"{self.registration.player} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if self.current_bid is None:
            self.current_bid = self.base_price
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        if self.registration.status != "APPROVED":
            errors["registration"] = (
                "Only approved registrations can enter the auction."
            )

        tournament = self.registration.tournament

        if (
            tournament.entry_fee > 0
            and self.registration.payment_status not in ["PAID", "WAIVED"]
        ):
            errors["registration"] = (
                "Payment must be verified or waived before the auction."
            )

        if self.winning_team and not tournament.teams.filter(
            pk=self.winning_team.pk
        ).exists():
            errors["winning_team"] = (
                "The winning team must belong to this tournament."
            )

        if self.status == "SOLD":
            if not self.winning_team:
                errors["winning_team"] = (
                    "Select the team that bought this player."
                )
            if self.final_price is None:
                errors["final_price"] = (
                    "Enter the final auction price."
                )

        if self.current_bid and self.current_bid < self.base_price:
            errors["current_bid"] = (
                "Current bid cannot be lower than the base price."
            )

        if errors:
            raise ValidationError(errors)

    def mark_sold(self, team, price):
        self.status = "SOLD"
        self.winning_team = team
        self.final_price = price
        self.current_bid = price
        self.completed_at = timezone.now()

        self.full_clean()
        self.save()

        team.players.add(self.registration.player)


class PointsTable(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="points_table",
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="points_entries",
    )

    matches_played = models.PositiveSmallIntegerField(default=0)
    wins = models.PositiveSmallIntegerField(default=0)
    losses = models.PositiveSmallIntegerField(default=0)
    ties = models.PositiveSmallIntegerField(default=0)
    no_results = models.PositiveSmallIntegerField(default=0)

    points = models.PositiveSmallIntegerField(default=0)

    net_run_rate = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-points", "-net_run_rate", "team__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "team"],
                name="unique_team_points_table_per_tournament",
            )
        ]

    def clean(self):
        if not self.tournament.teams.filter(pk=self.team_id).exists():
            raise ValidationError(
                {"team": "This team is not part of the selected tournament."}
            )

    def __str__(self):
        return f"{self.team} - {self.tournament}"