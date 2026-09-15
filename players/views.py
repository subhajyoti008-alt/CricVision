from django import forms
from django.contrib import admindocs
from players.models import Player
from .models import Team

# Create your views here.
class TeamAdminForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        available_players = Player.objects.filter(teams__isnull = True)

        if self.instance and self.instance.pk:
            current_team_players = Player.objects.filter(teams = self.instance)

            available_players = (
                available_players | current_team_players
            ).distinct()

        self.fields["players"].queryset = available_players.order_by(
            "full_name"
        )


        @admin.register(Team)
        class TeamAdmin(admin.ModelAdmin):
            form = TeamAdminForm

            list_display = ("name", "short_name", "city", "captain")
            search_fields = ("name", "short_name", "city")
            filter_horizontal = ("players",)