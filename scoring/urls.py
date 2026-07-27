from django.urls import path

from . import views

app_name = "scoring"

urlpatterns = [
    path("", views.scorer_home, name="scorer_home"),

    path(
        "innings/<int:innings_id>/setup/",
        views.innings_setup,
        name="innings_setup",
    ),

    path(
        "innings/<int:innings_id>/live/",
        views.live_scorer,
        name="live_scorer",
    ),

    path(
        "innings/<int:innings_id>/record-runs/",
        views.record_runs,
        name="record_runs",
    ),

    path(
        "innings/<int:innings_id>/wicket/",
        views.record_wicket,
        name="record_wicket",
    ),

    path(
        "innings/<int:innings_id>/new-bowler/",
        views.select_new_bowler,
        name="select_new_bowler",
    ),

    path(
        "innings/<int:innings_id>/finish/",
        views.finish_innings,
        name="finish_innings",
    ),
]