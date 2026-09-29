"""
One-time backfill: computes zone_area for shots imported before we started
capturing NBA's real SHOT_ZONE_AREA field directly.

This is a geometric APPROXIMATION (see zone_wedges.classify_zone_area) --
every shot imported from now on gets the authoritative value straight from
nba_api instead. Only run this against rows where zone_area is still blank;
it never touches a row that already has a real value.

Usage:
    py manage.py backfill_zone_area
    py manage.py backfill_zone_area --season 2025-26   (just one season)
"""

from django.core.management.base import BaseCommand
from library.models import Shot
from library.zone_wedges import classify_zone_area


class Command(BaseCommand):
    help = "Backfill zone_area for shots missing it, computed from stored loc_x/loc_y."

    def add_arguments(self, parser):
        parser.add_argument("--season", help="Only backfill this season (e.g. 2025-26).")

    def handle(self, *args, **options):
        shots = Shot.objects.filter(zone_area="")
        if options.get("season"):
            shots = shots.filter(season=options["season"])

        total = shots.count()
        if not total:
            self.stdout.write("Nothing to backfill -- every shot already has zone_area set.")
            return

        self.stdout.write(f"Backfilling zone_area for {total} shot(s) ...")

        updated = 0
        batch = []
        BATCH_SIZE = 1000

        for shot in shots.only("id", "loc_x", "loc_y", "zone_basic").iterator():
            shot.zone_area = classify_zone_area(shot.loc_x, shot.loc_y, shot.zone_basic)
            batch.append(shot)
            if len(batch) >= BATCH_SIZE:
                Shot.objects.bulk_update(batch, ["zone_area"])
                updated += len(batch)
                self.stdout.write(f"  {updated}/{total} done...")
                batch = []

        if batch:
            Shot.objects.bulk_update(batch, ["zone_area"])
            updated += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Done. Backfilled {updated} shot(s)."))
