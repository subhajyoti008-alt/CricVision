from django.contrib import admin
from players.models import Player
from .models import Delivery, Innings

class DeliveryInline(admin.TabularInline):
    model = Delivery
    extra = 1

    fields = (
        "sequence",
        "striker",
        "non_striker",
        "bowler",
        "runs_off_bat",
        "extras",
        "extra_type",
        "is_legal_delivery",
        "is_wicket",
        "wicket_player",
        "dismissal_kind",
    )

    def get_formset(self, request, obj=None, **kwrgs):
        formset = super().get_formset(request, obj, **kwrgs)

        if obj is not None:
            batting_players = Player.objects.filter(
                teams=obj.batting_team
            ).order_by("full_name")

            bowling_players = Player.objects.filter(
                teams=obj.bowling_team
            ).order_by("full_name")

            
            formset.form.base_fields["striker"].queryset = batting_players
            formset.form.base_fields["non_striker"].queryset = batting_players
            formset.form.base_fields["wicket_player"].queryset = batting_players
            formset.form.base_fields["bowler"].queryset = bowling_players

        return formset
    

@admin.register(Innings)
class InningsAdmin(admin.ModelAdmin):
    list_display = (
        "match",
        "number",
        "batting_team",
        "bowling_team",
        "target_runs",
        "is_completed",
    )

    list_filter = (
        "is_completed",
        "batting_team",
        "bowling_team",
    )

    inlines = [DeliveryInline]
