"""
Shared logic for the finer 14-zone breakdown (Restricted Area, Paint, both
corners unchanged; Mid-Range and Above the Break 3 each split into 5 angular
wedges: Left, Left-Center, Center, Right-Center, Right) -- matching the
resolution of a typical NBA broadcast/2K-style shot zone chart.

Two things live here:

1. classify_zone_area(loc_x, loc_y, zone_basic) -- a geometric approximation
   of nba_api's own SHOT_ZONE_AREA field, used ONLY to backfill shots that
   were imported before we started capturing the real field. Every shot
   imported from now on gets the authoritative value straight from nba_api
   (see import_shots.py / import_season.py) -- this function is a one-time
   backfill tool, not the source of truth going forward.

2. combined_zone_key(zone_basic, zone_area) / zone_display_label(...) -- the
   single place that decides how zone_basic + zone_area combine into one
   grouping key and a human-readable label. Used by both queries.py (player
   zone stats) and fetch_league_averages.py (the league baseline), so a
   shot and its league comparison are always keyed identically.
"""

import math

# Zones we split further by angle. Restricted Area, Paint, and both
# Corner-3s are left as single zones -- Corner-3 is already inherently one
# side, and splitting Restricted Area/Paint by angle isn't useful at this
# shot-chart's resolution.
SPLIT_BASIC_ZONES = {"Mid-Range", "Above the Break 3"}

AREA_KEYS = ["Left Side(L)", "Left Side Center(LC)", "Center(C)", "Right Side Center(RC)", "Right Side(R)"]

# Hoop position and 3pt radius/corner-break angle, matching the SVG
# coordinate convention in court-chart.js exactly (cx = 250 + loc_x,
# cy = 417 - loc_y), so the Python classification and the JS wedge geometry
# never disagree about where a boundary sits.
_CORNER_ANGLE = 67.750976  # angle from hoop to the corner-3 break point; must match court-chart.js exactly


def classify_zone_area(loc_x, loc_y, zone_basic):
    """Geometric approximation of SHOT_ZONE_AREA from shot location. Only
    meaningful for Mid-Range and Above the Break 3; returns "" for anything
    else (matching how those zones are stored -- no area split)."""
    if zone_basic not in SPLIT_BASIC_ZONES:
        return ""

    angle = math.degrees(math.atan2(loc_x, loc_y)) if (loc_x or loc_y) else 0.0

    if zone_basic == "Mid-Range":
        bounds = [-90, -54, -18, 18, 54, 90]
    else:  # Above the Break 3 (bounded by corner lines)
        bounds = [-_CORNER_ANGLE, -_CORNER_ANGLE * 0.6, -_CORNER_ANGLE * 0.2, _CORNER_ANGLE * 0.2, _CORNER_ANGLE * 0.6, _CORNER_ANGLE]

    for i in range(5):
        if bounds[i] <= angle <= bounds[i + 1]:
            return AREA_KEYS[i]
    # Outside the expected range (rare edge case / bad data) -- fall back to
    # whichever end it's closest to rather than leaving it unclassified.
    return AREA_KEYS[0] if angle < bounds[0] else AREA_KEYS[-1]


# Human-readable labels for the 10 split zones, keyed by (zone_basic, zone_area).
DISPLAY_LABELS = {
    ("Mid-Range", "Left Side(L)"): "Left Baseline Mid-Range",
    ("Mid-Range", "Left Side Center(LC)"): "Left Mid-Range",
    ("Mid-Range", "Center(C)"): "Center Mid-Range",
    ("Mid-Range", "Right Side Center(RC)"): "Right Mid-Range",
    ("Mid-Range", "Right Side(R)"): "Right Baseline Mid-Range",
    ("Above the Break 3", "Left Side(L)"): "Deep Left Wing 3",
    ("Above the Break 3", "Left Side Center(LC)"): "Left Wing 3",
    ("Above the Break 3", "Center(C)"): "Top of the Key 3",
    ("Above the Break 3", "Right Side Center(RC)"): "Right Wing 3",
    ("Above the Break 3", "Right Side(R)"): "Deep Right Wing 3",
}


def combined_zone_key(zone_basic, zone_area):
    """Stable grouping/lookup key combining zone_basic + zone_area. Blank
    zone_area (unsplit zones) just uses zone_basic alone."""
    if zone_area:
        return f"{zone_basic}|{zone_area}"
    return zone_basic


def zone_display_label(zone_basic, zone_area):
    """Human-readable label for a combined zone. Falls back to zone_basic
    itself for the four zones that aren't split."""
    if zone_area:
        return DISPLAY_LABELS.get((zone_basic, zone_area), f"{zone_basic} ({zone_area})")
    return zone_basic
