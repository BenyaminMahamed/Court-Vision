# library/urls.py — replace your existing file with this
from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.action_list, name="action_list"),
    path("actions/<slug:slug>/", views.action_detail, name="action_detail"),
    path("players/", views.player_list, name="player_list"),
    path("players/<int:pk>/", views.player_detail, name="player_detail"),

    # Clip pipeline
    path("clip-test/<str:game_id>/<int:event_id>/", views.clip_test, name="clip_test"),
    path("clip/<str:game_id>/<int:event_id>/", views.clip_stream, name="clip_stream"),
]