from django.urls import path

from . import views

app_name = "matches"

urlpatterns = [
    path("", views.match_list, name = "list"),
    path("<int:match_id>/", views.match_detail, name="detail"),
    path(
        "head-to-head/",
        views.head_to_head,
        name="head_to_head",
    ),
]