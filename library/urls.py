# library/urls.py — clean version, clip proxy routes removed
from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.action_list, name="action_list"),
    path("actions/<slug:slug>/", views.action_detail, name="action_detail"),
    path("players/", views.player_list, name="player_list"),
    path("players/<int:pk>/", views.player_detail, name="player_detail"),
]