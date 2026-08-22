from django.urls import path

from . import api_views

app_name = "api"

urlpatterns = [
    path("players/", api_views.PlayerListAPIView.as_view(), name="player_list"),
    path("players/<int:pk>/shotchart/", api_views.PlayerShotChartAPIView.as_view(), name="player_shotchart"),
    path("shots/", api_views.ShotListAPIView.as_view(), name="shot_list"),
    path("actions/", api_views.ActionListAPIView.as_view(), name="action_list"),
    path("actions/<slug:slug>/", api_views.ActionDetailAPIView.as_view(), name="action_detail"),
]
