"""
Management command to fetch league-wide FG% by shot zone from nba_api and
cache it locally — the baseline for the "X% above/below league average"
comparison on player zone heatmaps.

Run LOCALLY only (stats.nba.com blocks Render's datacenter IPs), same as
import_shots. Uses ShotChartDetail with player_id=0, team_id=0: nba_api
returns a second dataframe alongside the shot list that's already the
league-wide breakdown by zone — so this is one request per season, not
one per player. Safe to re-run: existing rows are updated, not duplicated.

Usage (PowerShell):
    py manage.py fetch_league_averages --season 2023-24
    py manage.py fetch_league_averages --season 2023-24 --season 2024-25
"""

import time

from django.core.management.base import BaseCommand, CommandError
from library.models import LeagueZoneAverage


class Command(BaseCommand):
    help = "Fetch and cache league-wide FG% by shot zone for one or more seasons."

    def add_arguments(self, parser):
        parser.add_argument("--season", action="append", required=True,
                            help='Season like 2023-24. Repeat the flag for multiple seasons.')

    def handle(self, *args, **options):
        try:
            from nba_api.stats.endpoints import shotchartdetail
        except ImportError:
            raise CommandError("nba_api is not installed in this environment. Run: pip install nba_api")

        seasons = options["season"]
        total_zones = 0

        for season in seasons:
            self.stdout.write(f"\nFetching league averages for {season} ...")

            try:
                resp = shotchartdetail.ShotChartDetail(
                    team_id=0,
                    player_id=0,
                    context_measure_simple="FGA",
                    season_nullable=season,
                    season_type_all_star="Regular Season",
                    timeout=30,
                )
                league_df = resp.get_data_frames()[1]
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Fetch failed for {season}: {e}"))
                continue

            if league_df.empty:
                self.stdout.write(self.style.WARNING(f"  No league data returned for {season}."))
                continue

            grouped = league_df.groupby("SHOT_ZONE_BASIC")[["FGA", "FGM"]].sum()

            for zone_basic, row in grouped.iterrows():
                attempts = int(row["FGA"])
                makes = int(row["FGM"])
                if attempts <= 0:
                    continue
                LeagueZoneAverage.objects.update_or_create(
                    season=season, zone_basic=zone_basic,
                    defaults={"attempts": attempts, "makes": makes},
                )
                total_zones += 1
                pct = 100 * makes / attempts
                self.stdout.write(f"  {zone_basic}: {makes}/{attempts} ({pct:.1f}%)")

            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"\nDone. {total_zones} zone-season rows cached."))
