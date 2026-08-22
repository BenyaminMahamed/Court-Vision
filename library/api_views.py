from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Action, Player, Shot
from .queries import get_player_shot_data
from .serializers import ActionSerializer, PlayerSerializer, ShotSerializer
from .shot_types import category_expression


class PlayerListAPIView(generics.ListAPIView):
    """GET /api/players/ — paginated list of players who have shot data."""
    serializer_class = PlayerSerializer

    def get_queryset(self):
        return (
            Player.objects
            .annotate(shot_count=Count("shots"))
            .filter(shot_count__gt=0)
            .order_by("name")
        )


class PlayerShotChartAPIView(APIView):
    """
    GET /api/players/<id>/shotchart/?season=&type=

    Composite endpoint: totals, seasons, shot types, zone splits, and the
    filtered shot list — built from the same shared query layer that
    renders the HTML player_detail page, so the numbers can never diverge.
    This is what the comparison page fetches, twice, to draw both charts.
    """

    def get(self, request, pk):
        player = get_object_or_404(Player, pk=pk)
        season = request.query_params.get("season")
        shot_type = request.query_params.get("type")
        data = get_player_shot_data(player, season=season, shot_type=shot_type)
        return Response({
            "player": PlayerSerializer(player).data,
            **data,
        })


class ShotListAPIView(generics.ListAPIView):
    """GET /api/shots/?player=<id>&season=&type= — conventional paginated/filterable resource."""
    serializer_class = ShotSerializer

    def get_queryset(self):
        qs = Shot.objects.all().order_by("-game_date")

        player_id = self.request.query_params.get("player")
        if player_id:
            qs = qs.filter(player_id=player_id)

        season = self.request.query_params.get("season")
        if season:
            qs = qs.filter(season=season)

        shot_type = self.request.query_params.get("type")
        if shot_type:
            qs = qs.annotate(shot_category=category_expression()).filter(shot_category=shot_type)

        return qs


class ActionListAPIView(generics.ListAPIView):
    serializer_class = ActionSerializer
    queryset = Action.objects.filter(is_published=True).order_by("name")


class ActionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ActionSerializer
    queryset = Action.objects.filter(is_published=True)
    lookup_field = "slug"
