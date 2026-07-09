"""
Backfill the `team` field on existing Player rows using TEAM_ABBREVIATION
from LeagueDashPlayerStats. Run locally (against Neon via $env:DATABASE_URL).

Usage:
    python manage.py backfill_teams --season 2025-26
"""

from django.core.management.base import BaseCommand, CommandError
from library.models import Player


class Command(BaseCommand):
    help = "Populate Player.team from NBA team abbreviations for a season."

    def add_arguments(self, parser):
        parser.add_argument("--season", required=True, help="e.g. 2025-26")

    def handle(self, *args, **options):
        try:
            from nba_api.stats.endpoints import leaguedashplayerstats
        except ImportError:
            raise CommandError("nba_api not installed.")

        season = options["season"]
        self.stdout.write(f"Fetching team abbreviations for {season} ...")

        try:
            df = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star="Regular Season",
                per_mode_detailed="Totals",
                timeout=30,
            ).get_data_frames()[0]
        except Exception as e:
            raise CommandError(f"Fetch failed: {e}")

        # Map nba player id -> team abbreviation
        team_by_id = {
            int(r["PLAYER_ID"]): str(r["TEAM_ABBREVIATION"])
            for _, r in df.iterrows()
        }

        updated = 0
        missing = 0
        for player in Player.objects.all():
            if player.nba_api_id in team_by_id:
                abbr = team_by_id[player.nba_api_id]
                if abbr and player.team != abbr:
                    player.team = abbr
                    player.save(update_fields=["team"])
                    updated += 1
            else:
                missing += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated {updated} players. {missing} not found in {season} stats."
        ))