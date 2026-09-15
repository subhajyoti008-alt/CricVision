from django.urls import path

from . import views


app_name = "tournaments"

urlpatterns = [
    path(
        "register/",
        views.player_register,
        name="player_register",
    ),
    path(
        "register/success/",
        views.registration_success,
        name = "registration_success",
    ),
]