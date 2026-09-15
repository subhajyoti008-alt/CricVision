from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import PlayerTournamentRegistrationForm


# Create your views here.

@require_http_methods(["GET", "POST"])
def player_register(request):
    if request.method == "GET":
        return JsonResponse(
            {
                "message": (
                    "Send a POST request to register "
                    "a player for a tournament."
                )
            }
        )

    form = PlayerTournamentRegistrationForm(
        request.POST
    )

    if not form.is_valid():
        return JsonResponse(
            {
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )

    registration = form.save()

    return JsonResponse(
        {
            "message": "Registration submitted successfully.",
            "registration_id": registration.id,
            "player": registration.player.full_name,
            "tournament": registration.tournament.name,
            "status": registration.status,
            "payment_status": registration.payment_status,
        },
        status=201,
    )


