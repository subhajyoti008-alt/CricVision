from django.shortcuts import render, get_object_or_404
from .models import Match

# Create your views here.
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
        ).prefetch_related(
            "innings__batting_team",
            "innings__bowling_team",
        ),
        pk=match_id,
    )

    return render(
        request,
        "matches/match_detail.html",
        {"match": match},
    )