
from django.db.models import Q
from teams.models import Team
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


def head_to_head(request):
    teams = Team.objects.order_by("name")

    team_a_id = request.GET.get("team_a")
    team_b_id = request.GET.get("team_b")

    if team_a_id and team_b_id:
        team_a = teams.filter(pk=team_a_id).first()
        team_b = teams.filter(pk=team_b_id).first()

    else:
        latest_match = Match.objects.filter(
            status="COMPLETED"
        ).select_related(
            "home_team",
            "away_team",
        ).order_by("-scheduled_at").first()

        if latest_match:
            team_a = latest_match.home_team
            team_b = latest_match.away_team
        else:
            team_a = None
            team_b = None

    context = {
        "teams": teams,
        "team_a": team_a,
        "team_b": team_b,
    }

    matches = list(
        Match.objects.filter(
            status = "COMPLETED"
        ).filter(
            Q(home_team=team_a, away_team=team_b) 
            | Q(home_team=team_b, away_team=team_a)
        ).select_related(
            "home_team",
            "away_team",
            "winner",
        ).prefetch_related(
            "innings__batting_team"
        ).order_by("-scheduled_at")
    )

    team_a_wins = 0
    team_b_wins = 0
    ties = 0
    team_a_runs = 0
    team_b_runs = 0

    for match in matches:
        if match.winner_id == team_a.id:
            team_a_wins += 1
        elif match.winner_id == team_b.id:
            team_b_wins += 1
        else:
            ties += 1

        for innings in match.innings.all():
            if innings.batting_team_id == team_a.id:
                team_a_runs += innings.total_runs

            elif innings.batting_team_id == team_b.id:
                team_b_runs += innings.total_runs

    context["stats"] = {
        "matches_played" : len(matches),
        "team_a_wins" : team_a_wins,
        "team_b_wins" : team_b_wins,
        "ties" : ties,
        "team_a_runs" : team_a_runs,
        "team_b_runs" : team_b_runs,
    }

    context["recent_matches"] = matches[:5]

    return render(
        request,
        "matches/head_to_head.html",
        context,
    )