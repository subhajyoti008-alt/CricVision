from django.contrib import admin

from .models import Match

# Register your models here.
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "home_team",
        "away_team",
        "tournament",
        "scheduled_at",
        "status",
    )

    list_filter = ("status", "tournament")
    search_fields = (
        "home_team_name",
        "away_team_name",
        "venue",
    )