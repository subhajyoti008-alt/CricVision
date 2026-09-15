from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import PlayerTournamentRegistrationForm


@require_http_methods(["GET", "POST"])
def player_register(request):
    if request.method == "POST":
        form = PlayerTournamentRegistrationForm(
            request.POST
        )

        if form.is_valid():
            form.save()

            return redirect(
                "tournaments:registration_success"
            )
    else:
        form = PlayerTournamentRegistrationForm()

    return render(
        request,
        "tournaments/player_register.html",
        {"form": form},
    )


def registration_success(request):
    return render(
        request,
        "tournaments/registration_success.html",
    )