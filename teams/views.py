from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Team

# Create your views here.

def team_list(request):
    teams = Team.objects.annotate(
        player_count = Count("players")
    ).order_by("name")

    return render(request, "teams/team_list.html", {"teams": teams})

def team_detail(request, team_id):
    team = get_object_or_404(
        Team.objects.prefetch_related("players"),
        pk=team_id,
    )

    return render(request, "teams/team_detail.html", {"team": team})
