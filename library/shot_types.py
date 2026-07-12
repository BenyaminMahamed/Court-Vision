"""
Buckets nba_api's granular ACTION_TYPE strings (e.g. "Pullup Jump shot",
"Driving Layup Shot", "Turnaround Fadeaway shot") into a handful of shot
types coaches actually think and talk in.

Single source of truth: `category_expression()` builds one Case/When SQL
expression, used both to filter shots by type and to compute per-type
counts for the filter UI. There is no second, Python-side copy of this
logic — so the two can never quietly drift apart.

Caveat: nba_api's raw ACTION_TYPE has no explicit "catch-and-shoot" tag.
A plain "Jump Shot" with no qualifier (no recorded dribble move before it)
is the closest available proxy, not a guarantee. Good enough as a first
cut; can be tightened later if a better signal becomes available.
"""

from django.db.models import Case, When, Value, CharField

CATEGORY_LABELS = {
    "pullup": "Pull-Up",
    "catch_shoot": "Catch & Shoot",
    "rim": "At the Rim",
    "post": "Post & Turnaround",
    "other": "Other",
}

# Order matters — Case/When evaluates top to bottom, first match wins.
# Most specific patterns go first so e.g. "Driving Floating Jump Shot"
# lands in pull-up rather than being caught by the generic "jump shot" rule.
_RULES = [
    ("pullup", r"(pullup|pull-up|step ?back|driving jump|driving floating|driving bank)"),
    ("rim", r"(layup|dunk|tip)"),
    ("post", r"(turnaround|hook|fadeaway)"),
    ("catch_shoot", r"(jump shot|bank shot)"),
]


def category_expression(field_name="action_type"):
    """A queryset-annotatable Case expression mapping action_type -> category key."""
    whens = [
        When(**{f"{field_name}__iregex": pattern}, then=Value(key))
        for key, pattern in _RULES
    ]
    return Case(*whens, default=Value("other"), output_field=CharField())