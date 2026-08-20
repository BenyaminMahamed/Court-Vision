"""
Checks every stored Example's YouTube video against YouTube's oEmbed endpoint
to flag ones that will silently fail to embed on the site.

This is a read-only report, not a fix — the actual cause (an uploader
disabling embedding on their video, most common on official NBA/team
highlight channels) can't be worked around from our side. Better to catch it
here, before publishing, than to find a broken player on the live action page.

Usage:
    python manage.py check_embeds
    python manage.py check_embeds --action pistol-action   # just one action's clips
"""

import requests
from django.core.management.base import BaseCommand
from library.models import Example


class Command(BaseCommand):
    help = "Reports which Example YouTube IDs are embeddable, blocked, or missing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--action", help="Only check clips belonging to this Action's slug."
        )

    def handle(self, *args, **options):
        examples = Example.objects.select_related("action").all()
        if options.get("action"):
            examples = examples.filter(action__slug=options["action"])

        total = examples.count()
        if not total:
            self.stdout.write("No matching examples found.")
            return

        ok = blocked = missing = errored = 0

        for ex in examples:
            oembed_url = (
                "https://www.youtube.com/oembed"
                f"?url=https://www.youtube.com/watch?v={ex.youtube_id}&format=json"
            )
            label = f"{ex.action.name} / {ex.title} ({ex.youtube_id})"

            try:
                resp = requests.get(oembed_url, timeout=8)
            except requests.RequestException as e:
                errored += 1
                self.stdout.write(self.style.WARNING(f"  ?        {label} — request failed: {e}"))
                continue

            if resp.status_code == 200:
                ok += 1
            elif resp.status_code in (401, 403):
                blocked += 1
                self.stdout.write(self.style.ERROR(
                    f"  BLOCKED  {label} — embedding disabled by the uploader"
                ))
            elif resp.status_code == 404:
                missing += 1
                self.stdout.write(self.style.ERROR(
                    f"  MISSING  {label} — video not found (deleted, private, or wrong ID)"
                ))
            else:
                errored += 1
                self.stdout.write(self.style.WARNING(
                    f"  ?        {label} — unexpected status {resp.status_code}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\n{ok} embeddable, {blocked} blocked, {missing} missing, {errored} errored — {total} total."
        ))