"""
Test command: fetch the VideoEvents clip URL for ONE shot and print it.
Purpose: confirm the endpoint works AND let us test whether the .mp4
plays in a plain browser <video> tag (the gating question).

Run locally (nba_api works locally). DB pointing at Neon is fine — read-only.

Usage:
    python manage.py test_clip --player "Alperen Sengun"
"""

from django.core.management.base import BaseCommand, CommandError
from library.models import Player, Shot


class Command(BaseCommand):
    help = "Fetch and print the video URL for one of a player's shots."

    def add_arguments(self, parser):
        parser.add_argument("--player", required=True)

    def handle(self, *args, **options):
        try:
            from nba_api.stats.endpoints import videoeventsasset
        except ImportError:
            raise CommandError("nba_api not installed.")

        name = options["player"]
        try:
            player = Player.objects.get(name__iexact=name)
        except Player.DoesNotExist:
            raise CommandError(f'No player "{name}" in the database.')

        # Grab one made shot (more likely to have clean video)
        shot = player.shots.filter(made=True).first()
        if not shot:
            shot = player.shots.first()
        if not shot:
            raise CommandError("That player has no shots stored.")

        self.stdout.write(f"Testing shot: {shot}")
        self.stdout.write(f"game_id={shot.game_id}  event_id={shot.game_event_id}")

        try:
            va = videoeventsasset.VideoEventsAsset(
                game_id=shot.game_id,
                game_event_id=shot.game_event_id,
                timeout=30,
            )
            data = va.get_dict()
        except Exception as e:
            raise CommandError(f"VideoEvents call failed: {e}")

        try:
            urls = data["resultSets"]["Meta"]["videoUrls"]
        except (KeyError, IndexError, TypeError):
            self.stdout.write(self.style.ERROR("No videoUrls in response. Raw keys:"))
            self.stdout.write(str(list(data.get("resultSets", {}).keys())))
            return

        if not urls:
            self.stdout.write(self.style.WARNING("videoUrls list is empty — no clip for this shot."))
            return

        u = urls[0]
        self.stdout.write(self.style.SUCCESS("\n--- CLIP URLS ---"))
        for key in ("lurl", "murl", "surl"):
            if u.get(key):
                self.stdout.write(f"{key}: {u[key]}")
        self.stdout.write(self.style.SUCCESS(
            "\nTest: paste the lurl into a browser tab. If it plays/downloads, "
            "an on-site <video> tag will likely work. If it errors/403s, we need a proxy."
        ))