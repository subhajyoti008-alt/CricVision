from django.shortcuts import get_object_or_404, render

from players.models import Player
from .models import Match


def build_innings_scorecard(innings):
    deliveries = list(
        innings.deliveries.select_related(
            "striker",
            "non_striker",
            "bowler",
            "wicket_player",
        )
    )

    batting_player_ids = {
        delivery.striker_id for delivery in deliveries
    } | {
        delivery.non_striker_id for delivery in deliveries
    }

    batting_players = Player.objects.filter(
        pk__in=batting_player_ids
    ).order_by("full_name")

    batting_rows = []

    for player in batting_players:
        faced_deliveries = [
            delivery
            for delivery in deliveries
            if delivery.striker_id == player.id
        ]

        runs = sum(
            delivery.runs_off_bat
            for delivery in faced_deliveries
        )

        balls = sum(
            1
            for delivery in faced_deliveries
            if delivery.is_legal_delivery
        )

        fours = sum(
            1
            for delivery in faced_deliveries
            if delivery.runs_off_bat == 4
        )

        sixes = sum(
            1
            for delivery in faced_deliveries
            if delivery.runs_off_bat == 6
        )

        is_out = any(
            delivery.wicket_player_id == player.id
            for delivery in deliveries
        )

        strike_rate = "-"

        if balls > 0:
            strike_rate = f"{(runs / balls) * 100:.2f}"

        batting_rows.append(
            {
                "player": player,
                "runs": runs,
                "balls": balls,
                "fours": fours,
                "sixes": sixes,
                "strike_rate": strike_rate,
                "is_out": is_out,
            }
        )

    bowler_ids = {
        delivery.bowler_id for delivery in deliveries
    }

    bowlers = Player.objects.filter(
        pk__in=bowler_ids
    ).order_by("full_name")

    bowling_rows = []

    for bowler in bowlers:
        bowled_deliveries = [
            delivery
            for delivery in deliveries
            if delivery.bowler_id == bowler.id
        ]

        legal_balls = sum(
            1
            for delivery in bowled_deliveries
            if delivery.is_legal_delivery
        )

        overs, balls = divmod(legal_balls, 6)

        runs_conceded = sum(
            delivery.runs_off_bat
            for delivery in bowled_deliveries
        )

        runs_conceded += sum(
            delivery.extras
            for delivery in bowled_deliveries
            if delivery.extra_type not in ["BYE", "LEG_BYE"]
        )

        wickets = sum(
            1
            for delivery in bowled_deliveries
            if delivery.is_wicket
        )

        economy = "-"

        if legal_balls > 0:
            economy = f"{(runs_conceded * 6) / legal_balls:.2f}"

        bowling_rows.append(
            {
                "player": bowler,
                "overs": f"{overs}.{balls}",
                "runs_conceded": runs_conceded,
                "wickets": wickets,
                "economy": economy,
            }
        )

    return {
        "innings": innings,
        "batting_rows": batting_rows,
        "bowling_rows": bowling_rows,
    }


def match_list(request):
    matches = Match.objects.select_related(
        "home_team",
        "away_team",
        "tournament",
        "winner",
    ).order_by("-scheduled_at")

    return render(
        request,
        "matches/match_list.html",
        {"matches": matches},
    )


def match_detail(request, match_id):
    match = get_object_or_404(
        Match.objects.select_related(
            "home_team",
            "away_team",
            "tournament",
            "winner",
        ),
        pk=match_id,
    )

    innings_scorecards = [
        build_innings_scorecard(innings)
        for innings in match.innings.all()
    ]

    return render(
        request,
        "matches/match_detail.html",
        {
            "match": match,
            "innings_scorecards": innings_scorecards,
        },
    )