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
    path(
        "payments/<int:registration_id>/",
        views.payment_submit,
        name="payment_submit",
    ),
    path(
        "register/success/<int:registration_id>/",
        views.registration_success,
        name="registration_success",
    ),
]