from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import (PlayerTournamentRegistrationForm, PlayerPaymentForm,)
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import Registration
from .services import submit_player_payment


@require_http_methods(["GET", "POST"])
def player_register(request):
    if request.method == "POST":
        form = PlayerTournamentRegistrationForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            registration = form.save()

            login(
                request,
                registration.player.user,
            )

            return redirect(
                "tournaments:registration_success",
                registration_id=registration.id,
            )
    else:
        form = PlayerTournamentRegistrationForm()

    return render(
        request,
        "tournaments/player_register.html",
        {"form": form},
    )


@login_required
def registration_success(request,registration_id):
    registration = get_object_or_404(
        Registration,
        pk=registration_id,
        player__user=request.user,
    )
    return render(
        request,
        "tournaments/registration_success.html",
        {"registration": registration},
    )

@login_required
@require_http_methods(["GET", "POST"])
def payment_submit(request, registration_id):
    registration = get_object_or_404(
        Registration,
        pk=registration_id,
        player__user=request.user,
    )

    if request.method == "POST":
        form = PlayerPaymentForm(request.POST)

        if form.is_valid():
            try:
                submit_player_payment(
                    registration=registration,
                    user=request.user,
                    method=form.cleaned_data["method"],
                    transaction_reference=form.cleaned_data[
                        "transaction_reference"
                    ],
                )
            except ValidationError as error:
                form.add_error(
                    None,
                    error.messages,
                )
            else:
                return redirect(
                    "tournaments:registration_success",
                    registration_id=registration.id,
                )
    else:
        form = PlayerPaymentForm()

    return render(
        request,
        "tournaments/payment_submit.html",
        {
            "form": form,
            "registration": registration,
        },
    )