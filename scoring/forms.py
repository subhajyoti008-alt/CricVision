from django import forms

from players.models import Player


class InningsSetupForm(forms.Form):

    striker = forms.ModelChoiceField(
        queryset = Player.objects.none(),
        label = "Opening striker",
    )

    non_striker = forms.ModelChoiceField(
        queryset = Player.objects.none(),
        label = "Opening non_striker",
    )

    bowler = forms.ModelChoiceField(
        queryset = Player.objects.none(),
        label = "First bowler",
    )

    def __init__(self, *args, innings, **kwargs):
        super().__init__(*args, **kwargs)

        batting_players = Player.objects.filter(
            teams = innings.batting_team
        ).order_by("full_name")

        bowling_players = Player.objects.filter(
            teams = innings.bowling_team
        ).order_by("full_name")

        self.fields["striker"].queryset = batting_players
        self.fields["non_striker"].queryset = batting_players
        self.fields["bowler"].queryset = bowling_players

    def clean(self):
        cleaned_data = super().clean()

        striker = cleaned_data.get("striker")
        non_striker = cleaned_data.get("non_striker")

        if striker and non_striker and striker == non_striker:
            raise forms.ValidationError(
                "Striker and non-striker must be different players."
            )
        
        return cleaned_data 
    

class NewBowlerForm(forms.Form):
    bowler = forms.ModelChoiceField(
        queryset = Player.objects.none(),
        label = "Bowler for the next over",
    )

    def __init__(self, *args, innings, **kwargs):
        super().__init__(*args, **kwargs)

        bowlers = Player.objects.filter(
            teams = innings.bowling_team
        ).exclude(
            pk = innings.current_bowler_id
        ).order_by("full_name")

        self.fields["bowler"].queryset = bowlers

class WicketForm(forms.Form):
    dismissed_player = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        label="Dismissed player",
    )

    next_batter = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        required=False,
        label="New batter",
        help_text="Leave blank only if the innings is over.",
    )

    def __init__(self, *args, innings, **kwargs):
        super().__init__(*args, **kwargs)

        current_batters = Player.objects.filter(
            pk__in=[
                innings.current_striker_id,
                innings.current_non_striker_id,
            ]
        )

        dismissed_player_ids = innings.deliveries.filter(
            is_wicket=True
        ).values_list("wicket_player_id", flat=True)

        available_batters = Player.objects.filter(
            teams=innings.batting_team
        ).exclude(
            pk__in=[
                innings.current_striker_id,
                innings.current_non_striker_id,
            ]
        ).exclude(
            pk__in=dismissed_player_ids
        ).order_by("full_name")

        self.fields["dismissed_player"].queryset = current_batters
        self.fields["next_batter"].queryset = available_batters
