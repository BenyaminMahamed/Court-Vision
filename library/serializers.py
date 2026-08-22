from rest_framework import serializers

from .models import Action, Player, Shot


class PlayerSerializer(serializers.ModelSerializer):
    headshot_url = serializers.ReadOnlyField()
    shot_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Player
        fields = ["id", "name", "team", "nba_api_id", "headshot_url", "shot_count"]


class ShotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shot
        fields = [
            "id", "player", "game_id", "game_event_id", "game_date", "season",
            "loc_x", "loc_y", "shot_distance", "made", "shot_value",
            "action_type", "shot_type", "zone_basic", "zone_range",
        ]


class ActionSerializer(serializers.ModelSerializer):
    alias_list = serializers.ReadOnlyField()
    play_type_list = serializers.ReadOnlyField()

    class Meta:
        model = Action
        fields = [
            "id", "name", "slug", "category", "difficulty",
            "breakdown", "key_reads", "alias_list", "play_type_list", "is_published",
        ]
