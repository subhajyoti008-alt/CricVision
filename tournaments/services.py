from django.db import transaction
from matches.models import Match

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from accounts.models import UserProfile
from players.models import Player

from .models import PointsTable, Registration


# Create Model:

def rebuild_points_table(tournament):
    teams = list(tournament.teams.all())

    if not teams:
        return

    with transaction.atomic():
        standings = {}

        for team in teams:
            standing, _ = PointsTable.objects.get_or_create(
                tournament=tournament,
                team=team,
            )

            standing.matches_played = 0
            standing.wins = 0
            standing.losses = 0
            standing.ties = 0
            standing.no_results = 0
            standing.points = 0

            standings[team.id] = standing

        completed_matches = Match.objects.filter(
            tournament=tournament,
            status__in=["COMPLETED", "ABANDONED"],
        )

        for match in completed_matches:
            home = standings.get(match.home_team_id)
            away = standings.get(match.away_team_id)

            if not home or not away:
                continue

            home.matches_played += 1
            away.matches_played += 1

            if match.status == "ABANDONED":
                home.no_results += 1
                away.no_results += 1
                home.points += 1
                away.points += 1

            elif match.winner_id == match.home_team_id:
                home.wins += 1
                away.losses += 1
                home.points += 2

            elif match.winner_id == match.away_team_id:
                away.wins += 1
                home.losses += 1
                away.points += 2

            else:
                home.ties += 1
                away.ties += 1
                home.points += 1
                away.points += 1

        for standing in standings.values():
            standing.save(
                update_fields=[
                    "matches_played",
                    "wins",
                    "losses",
                    "ties",
                    "no_results",
                    "points",
                    "updated_at",
                ]
            )


@transaction.atomic
def register_player_for_tournament(
    *,
    username,
    password,
    full_name,
    phone_number,
    tournament,
    email="",
    date_of_birth=None,
    city="",
    batting_style="RIGHT",
    bowling_style="NONE",
    is_wicketkeeper=False,
):
    User = get_user_model()

    username = username.strip()
    full_name = full_name.strip()
    phone_number = phone_number.strip()
    email = email.strip()

    if not username:
        raise ValidationError(
            {"username": "Username is required."}
        )

    if not full_name:
        raise ValidationError(
            {"full_name": "Player name is required."}
        )

    if not phone_number:
        raise ValidationError(
            {"phone_number": "Phone number is required."}
        )

    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError(
            {"username": "This username is already taken."}
        )

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
    )

    UserProfile.objects.create(
        user=user,
        role=UserProfile.Role.PLAYER,
        phone_number=phone_number,
    )

    player = Player.objects.create(
        user=user,
        full_name=full_name,
        date_of_birth=date_of_birth,
        city=city,
        batting_style=batting_style,
        bowling_style=bowling_style,
        is_wicketkeeper=is_wicketkeeper,
    )

    registration = Registration.objects.create(
        player=player,
        tournament=tournament,
    )

    return registration