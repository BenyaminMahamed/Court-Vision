"""
Management command to import a player's shots from nba_api into the Shot table.

Run LOCALLY only (stats.nba.com blocks Render's datacenter IPs).
Writes to whatever DATABASE_URL points at — so pointing at Neon locally
populates production. Safe to re-run: the unique (game_id, game_event_id)
constraint means existing shots are skipped, not duplicated.

Usage:
    python manage.py import_shots --player "Jalen Green" --season 2023-24
    python manage.py import_shots --player "Jalen Green" --season 2023-24 --season 2024-25
"""

import time
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from library.models import Player, Shot


class Command(BaseCommand):
    help = "Import a player's shot chart data from nba_api into the Shot table."

    def add_arguments(self, parser):
        parser.add_argument("--player", required=True, help='Full name, e.g. "Jalen Green"')
        parser.add_argument("--season", action="append", required=True,
                            help='Season like 2023-24. Repeat the flag for multiple seasons.')

    def handle(self, *args, **options):
        # Imported here (not at top) so the app doesn't require nba_api at runtime on Render.
        try:
            from nba_api.stats.static import players as static_players
            from nba_api.stats.endpoints import shotchartdetail
        except ImportError:
            raise CommandError("nba_api is not installed in this environment. Run: pip install nba_api")

        player_name = options["player"]
        seasons = options["season"]

        # --- 1. Resolve the player's NBA id ---
        matches = static_players.find_players_by_full_name(player_name)
        if not matches:
            raise CommandError(f'No NBA player found matching "{player_name}".')
        if len(matches) > 1:
            names = ", ".join(m["full_name"] for m in matches[:5])
            self.stdout.write(self.style.WARNING(f"Multiple matches, using first. Candidates: {names}"))
        nba_player = matches[0]
        nba_id = nba_player["id"]
        full_name = nba_player["full_name"]

        # --- 2. Get or create the local Player row ---
        player_obj, created = Player.objects.get_or_create(
            nba_api_id=nba_id,
            defaults={"name": full_name},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Player: {full_name} (nba_id {nba_id})"))
        else:
            self.stdout.write(f"Using existing Player: {full_name} (nba_id {nba_id})")

        total_new = 0

        for season in seasons:
            self.stdout.write(f"\nFetching shots for {full_name} — {season} ...")

            try:
                resp = shotchartdetail.ShotChartDetail(
                    team_id=0,
                    player_id=nba_id,
                    context_measure_simple="FGA",   # all field-goal attempts (makes + misses)
                    season_nullable=season,
                    season_type_all_star="Regular Season",
                    timeout=30,
                )
                df = resp.get_data_frames()[0]
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Fetch failed for {season}: {e}"))
                continue

            if df.empty:
                self.stdout.write(self.style.WARNING(f"  No shots returned for {season}."))
                continue

            new_this_season = 0
            for _, row in df.iterrows():
                # Parse game date (format like '20231025')
                game_date = None
                raw_date = str(row.get("GAME_DATE", "")).strip()
                if len(raw_date) == 8 and raw_date.isdigit():
                    game_date = datetime.strptime(raw_date, "%Y%m%d").date()

                shot_value = 3 if str(row.get("SHOT_TYPE", "")).startswith("3") else 2

                _, was_created = Shot.objects.get_or_create(
                    game_id=str(row["GAME_ID"]),
                    game_event_id=int(row["GAME_EVENT_ID"]),
                    defaults={
                        "player": player_obj,
                        "game_date": game_date,
                        "season": season,
                        "team_id": row.get("TEAM_ID") or None,
                        "loc_x": int(row["LOC_X"]),
                        "loc_y": int(row["LOC_Y"]),
                        "shot_distance": row.get("SHOT_DISTANCE") or None,
                        "made": bool(row["SHOT_MADE_FLAG"]),
                        "shot_value": shot_value,
                        "action_type": str(row.get("ACTION_TYPE", ""))[:60],
                        "shot_type": str(row.get("SHOT_TYPE", ""))[:20],
                        "zone_basic": str(row.get("SHOT_ZONE_BASIC", ""))[:40],
                        "zone_range": str(row.get("SHOT_ZONE_RANGE", ""))[:40],
                    },
                )
                if was_created:
                    new_this_season += 1

            total_new += new_this_season
            self.stdout.write(self.style.SUCCESS(
                f"  {season}: {len(df)} shots fetched, {new_this_season} new inserted."
            ))
            time.sleep(1)  # be gentle with stats.nba.com between seasons

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {total_new} new shots imported for {full_name}."
        ))