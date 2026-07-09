"""
Import shots for the most-used players in a season, ordered by total minutes.

Run LOCALLY only. Resumable: re-run after a timeout/block and it skips
players already imported for that season.

Usage:
    python manage.py import_season --season 2025-26 --limit 50
    python manage.py import_season --season 2025-26 --limit 5      (test run)
"""

import time
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from library.models import Player, Shot


class Command(BaseCommand):
    help = "Import shot data for the top-minutes players in a season."

    def add_arguments(self, parser):
        parser.add_argument("--season", required=True, help='e.g. 2025-26')
        parser.add_argument("--limit", type=int, default=50,
                            help="Import the top N players by minutes (default 50).")
        parser.add_argument("--sleep", type=float, default=1.2,
                            help="Seconds between player API calls (default 1.2).")

    def handle(self, *args, **options):
        try:
            from nba_api.stats.endpoints import leaguedashplayerstats, shotchartdetail
        except ImportError:
            raise CommandError("nba_api not installed. Run: pip install nba_api")

        season = options["season"]
        limit = options["limit"]
        sleep_s = options["sleep"]

        # --- 1. Get the season's players ranked by minutes ---
        self.stdout.write(f"Fetching player minutes leaders for {season} ...")
        try:
            resp = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star="Regular Season",
                per_mode_detailed="Totals",
                timeout=30,
            )
            df = resp.get_data_frames()[0]
        except Exception as e:
            raise CommandError(f"Failed to fetch player stats: {e}")

        if df.empty:
            raise CommandError(f"No player stats returned for {season}. Check the season string.")

        # Sort by total minutes, descending, take the top N
        df = df.sort_values("FGA", ascending=False).head(limit)
        ranked = [(int(r["PLAYER_ID"]), r["PLAYER_NAME"]) for _, r in df.iterrows()]

        self.stdout.write(self.style.SUCCESS(
            f"Top {len(ranked)} players by minutes for {season}. Starting import.\n"
        ))

        total_new = 0
        processed = 0
        skipped = 0

        for nba_id, name in ranked:
            processed += 1

            # Resumability: skip players already imported for this season.
            if Shot.objects.filter(player__nba_api_id=nba_id, season=season).exists():
                skipped += 1
                self.stdout.write(f"[{processed}/{len(ranked)}] {name} — already imported, skip.")
                continue

            player_obj, _ = Player.objects.get_or_create(
                nba_api_id=nba_id, defaults={"name": name}
            )

            try:
                sc = shotchartdetail.ShotChartDetail(
                    team_id=0,
                    player_id=nba_id,
                    context_measure_simple="FGA",
                    season_nullable=season,
                    season_type_all_star="Regular Season",
                    timeout=30,
                )
                shot_df = sc.get_data_frames()[0]
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{processed}/{len(ranked)}] {name} — fetch failed: {e}"))
                time.sleep(sleep_s)
                continue

            if shot_df.empty:
                self.stdout.write(f"[{processed}/{len(ranked)}] {name} — no shots.")
                time.sleep(sleep_s)
                continue

            new_here = 0
            for _, r in shot_df.iterrows():
                game_date = None
                raw = str(r.get("GAME_DATE", "")).strip()
                if len(raw) == 8 and raw.isdigit():
                    game_date = datetime.strptime(raw, "%Y%m%d").date()
                shot_value = 3 if str(r.get("SHOT_TYPE", "")).startswith("3") else 2

                _, created = Shot.objects.get_or_create(
                    game_id=str(r["GAME_ID"]),
                    game_event_id=int(r["GAME_EVENT_ID"]),
                    defaults={
                        "player": player_obj,
                        "game_date": game_date,
                        "season": season,
                        "team_id": r.get("TEAM_ID") or None,
                        "loc_x": int(r["LOC_X"]),
                        "loc_y": int(r["LOC_Y"]),
                        "shot_distance": r.get("SHOT_DISTANCE") or None,
                        "made": bool(r["SHOT_MADE_FLAG"]),
                        "shot_value": shot_value,
                        "action_type": str(r.get("ACTION_TYPE", ""))[:60],
                        "shot_type": str(r.get("SHOT_TYPE", ""))[:20],
                        "zone_basic": str(r.get("SHOT_ZONE_BASIC", ""))[:40],
                        "zone_range": str(r.get("SHOT_ZONE_RANGE", ""))[:40],
                    },
                )
                if created:
                    new_here += 1

            total_new += new_here
            self.stdout.write(self.style.SUCCESS(
                f"[{processed}/{len(ranked)}] {name} — {len(shot_df)} shots, {new_here} new."
            ))
            time.sleep(sleep_s)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone {season}. Processed {processed}, skipped {skipped}, {total_new} new shots imported."
        ))
        self.stdout.write(self.style.WARNING(
            "Check your Neon storage meter before importing more."
        ))