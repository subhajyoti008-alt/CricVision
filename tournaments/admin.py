from datetime import datetime, time, timedelta

from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from matches.models import Match

from .models import Auction, Payment, PointsTable, Registration, Tournament


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "competition_type",
        "city",
        "format",
        "start_date",
        "end_date",
        "is_published",
    )

    list_filter = (
        "competition_type",
        "format",
        "is_published",
        "city",
    )

    search_fields = ("name", "city", "venue")
    filter_horizontal = ("teams",)

    actions = ("generate_premier_league_fixtures",)

    @admin.action(
        description="Generate Premier League fixtures"
    )
    def generate_premier_league_fixtures(
        self,
        request,
        queryset,
    ):
        match_times = [
            time(8, 0),
            time(9, 30),
            time(11, 0),
            time(12, 30),
            time(14, 0),
            time(15, 30),
            time(17, 0),
            time(18, 30),
        ]

        for tournament in queryset:
            if tournament.competition_type != "PREMIER_LEAGUE":
                self.message_user(
                    request,
                    f"{tournament.name} is not a Premier League.",
                    level=messages.ERROR,
                )
                continue

            teams = list(
                tournament.teams.order_by("name")
            )

            if len(teams) != 5:
                self.message_user(
                    request,
                    f"{tournament.name} needs exactly 5 teams. "
                    f"It currently has {len(teams)}.",
                    level=messages.ERROR,
                )
                continue

            if tournament.matches.exists():
                self.message_user(
                    request,
                    f"{tournament.name} already has matches. "
                    "Fixtures were not generated again.",
                    level=messages.WARNING,
                )
                continue

            final_league_day = tournament.start_date + timedelta(days=2)

            if tournament.end_date < final_league_day:
                self.message_user(
                    request,
                    f"{tournament.name} needs at least 3 days "
                    "to schedule 20 league matches.",
                    level=messages.ERROR,
                )
                continue

            fixtures = []

            for first_index in range(len(teams)):
                for second_index in range(
                    first_index + 1,
                    len(teams),
                ):
                    team_a = teams[first_index]
                    team_b = teams[second_index]

                    fixtures.append((team_a, team_b))
                    fixtures.append((team_b, team_a))

            with transaction.atomic():
                for index, fixture in enumerate(fixtures):
                    home_team, away_team = fixture

                    match_date = (
                        tournament.start_date
                        + timedelta(days=index // 8)
                    )

                    match_time = match_times[index % 8]

                    scheduled_at = timezone.make_aware(
                        datetime.combine(match_date, match_time)
                    )

                    Match.objects.create(
                        tournament=tournament,
                        home_team=home_team,
                        away_team=away_team,
                        venue=tournament.venue,
                        scheduled_at=scheduled_at,
                        over_per_innings=tournament.over_per_innings,
                        status="SCHEDULED",
                        stage="LEAGUE",
                    )

            self.message_user(
                request,
                f"Created 20 league fixtures for {tournament.name}.",
                level=messages.SUCCESS,
            )

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "tournament",
        "status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "tournament",
    )

    search_fields = (
        "player__full_name",
        "tournament__name",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "registration",
        "method",
        "amount",
        "status",
        "verified_by",
        "created_at",
    )

    list_filter = (
        "method",
        "status",
    )

    search_fields = (
        "registration__player__full_name",
        "transaction_reference",
    )

    readonly_fields = (
        "verified_by",
        "verified_at",
        "created_at",
    )

    actions = ("verify_selected_payments",)

    @admin.action(description="Verify selected payments")
    def verify_selected_payments(self, request, queryset):
        verified_count = 0

        for payment in queryset:
            if payment.status != "VERIFIED":
                payment.verify(request.user)
                verified_count += 1

        self.message_user(
            request,
            f"{verified_count} payment(s) verified.",
            level=messages.SUCCESS,
        )


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = (
        "registration",
        "base_price",
        "current_bid",
        "status",
        "winning_team",
        "final_price",
    )

    list_filter = ("status",)

    search_fields = (
        "registration__player__full_name",
        "registration__tournament__name",
    )

    readonly_fields = (
        "listed_at",
        "completed_at",
    )

    def save_model(self, request, obj, form, change):
        if obj.status == "SOLD" and not obj.completed_at:
            obj.completed_at = timezone.now()

        super().save_model(request, obj, form, change)

        if obj.status == "SOLD" and obj.winning_team:
            obj.winning_team.players.add(
                obj.registration.player
            )


@admin.register(PointsTable)
class PointsTableAdmin(admin.ModelAdmin):
    list_display = (
        "team",
        "tournament",
        "matches_played",
        "wins",
        "losses",
        "ties",
        "points",
        "net_run_rate",
    )

    list_filter = ("tournament",)

    readonly_fields = (
        "tournament",
        "team",
        "matches_played",
        "wins",
        "losses",
        "ties",
        "no_results",
        "points",
        "net_run_rate",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False