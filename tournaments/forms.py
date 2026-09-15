from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from players.models import Player

from .models import Tournament
from .services import register_player_for_tournament


class PlayerTournamentRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)

    password = forms.CharField(
        widget=forms.PasswordInput,
    )

    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )

    email = forms.EmailField(
        required=False,
    )

    full_name = forms.CharField(max_length=120)

    phone_number = forms.CharField(max_length=15)

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date"},
        ),
    )

    city = forms.CharField(
        max_length=80,
        required=False,
    )

    batting_style = forms.ChoiceField(
        choices=Player.BATTING_STYLES,
        initial="RIGHT",
    )

    bowling_style = forms.ChoiceField(
        choices=Player.BOWLING_STYLES,
        initial="NONE",
    )

    is_wicketkeeper = forms.BooleanField(
        required=False,
    )

    tournament = forms.ModelChoiceField(
        queryset=Tournament.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tournament"].queryset = (
            Tournament.objects.filter(
                is_published=True,
            ).order_by("-start_date", "name")
        )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        User = get_user_model()

        if User.objects.filter(
            username__iexact=username,
        ).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get(
            "password_confirm"
        )

        if password and password_confirm:
            if password != password_confirm:
                self.add_error(
                    "password_confirm",
                    "Passwords do not match.",
                )

        return cleaned_data

    def save(self):
        if not self.is_valid():
            raise ValueError(
                "Call is_valid() before save()."
            )

        return register_player_for_tournament(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            email=self.cleaned_data["email"],
            full_name=self.cleaned_data["full_name"],
            phone_number=self.cleaned_data["phone_number"],
            date_of_birth=self.cleaned_data[
                "date_of_birth"
            ],
            city=self.cleaned_data["city"],
            batting_style=self.cleaned_data[
                "batting_style"
            ],
            bowling_style=self.cleaned_data[
                "bowling_style"
            ],
            is_wicketkeeper=self.cleaned_data[
                "is_wicketkeeper"
            ],
            tournament=self.cleaned_data["tournament"],
        )
    