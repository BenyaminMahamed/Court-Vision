"""
Shared shot-query layer for player shot data.

Single source of truth for turning a Player + season/type filters into
totals, zone splits, and a plotted shot list. Both the HTML player_detail
view and the shotchart API call get_player_shot_data(), so there is
exactly one place this math happens — not two copies that can quietly
drift apart.
"""
from django.db.models import Count, Q

from .models import LeagueZoneAverage
from .zone_wedges import combined_zone_key, zone_display_label, SPLIT_BASIC_ZONES
from .shot_types import category_expression, CATEGORY_LABELS

# Below this many attempts in a zone, we don't compute a league-average
# diff for it — a handful of corner-3 attempts reading "+22% vs league"
# is noise, not signal.
MIN_ZONE_ATTEMPTS_FOR_COMPARISON = 15

AREA_SHORT = {
    "Center(C)": "Center",
    "Left Side(L)": "Left",
    "Right Side(R)": "Right",
    "Left Side Center(LC)": "Left Center",
    "Right Side Center(RC)": "Right Center",
    "Back Court(BC)": "Back Court",
}
NO_AREA_PREFIX = ("Restricted Area", "Backcourt", "Left Corner 3", "Right Corner 3")


def zone_key_and_label(basic, area):
    """Return (internal key, human-readable label) for a basic zone + area."""
    if not area:
        return basic, basic
    key = basic + "|" + area
    if basic in NO_AREA_PREFIX:
        return key, basic
    return key, AREA_SHORT.get(area, area) + " " + basic


def get_player_shot_data(player, season=None, shot_type=None, url_for_season=None, url_for_type=None):
    """
    Returns a dict of everything a shot chart needs for `player`, filtered
    by `season` and `shot_type` if given and valid:

        total, made, fg_pct, shown_count,
        seasons, season_pills, active_season,
        shot_types, active_type,
        shot_points, zone_stats

    zone_stats entries now also carry `league_pct` and `diff` (player pct
    minus league pct) when a single season is selected and cached league
    averages exist for it and the zone; otherwise both are None.
    """
    shots = player.shots.all()

    seasons = list(shots.values_list("season", flat=True).distinct().order_by("season"))
    if season and season in seasons:
        shots = shots.filter(season=season)

    shots = shots.annotate(shot_category=category_expression())

    type_counts = (
        shots.values("shot_category")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    shot_types = []
    valid_type_keys = set()
    for row in type_counts:
        if row["n"] <= 0:
            continue
        valid_type_keys.add(row["shot_category"])
        entry = {
            "key": row["shot_category"],
            "label": CATEGORY_LABELS.get(row["shot_category"], row["shot_category"]),
            "count": row["n"],
            "active": row["shot_category"] == shot_type,
        }
        if url_for_type:
            entry["url"] = url_for_type(row["shot_category"])
        shot_types.append(entry)

    if shot_type and shot_type in valid_type_keys:
        shots = shots.filter(shot_category=shot_type)

    total = shots.count()
    made = shots.filter(made=True).count()

    shot_points = [
        {
            "x": s.loc_x, "y": s.loc_y, "made": s.made, "v": s.shot_value,
            "gid": s.game_id, "eid": s.game_event_id, "season": s.season,
        }
        for s in shots
    ]

    raw_zones = (
        shots.values("zone_basic", "zone_area")
        .annotate(attempts=Count("id"), makes=Count("id", filter=Q(made=True)))
    )

    # nba_api fills zone_area for every shot, but we only split Mid-Range and
    # Above the Break 3 by area. Everything else collapses back to one zone.
    zone_totals = {}
    for z in raw_zones:
        basic = z["zone_basic"]
        if not basic:
            continue
        area = z["zone_area"] if basic in SPLIT_BASIC_ZONES else ""
        key = combined_zone_key(basic, area)
        t = zone_totals.setdefault(key, {"basic": basic, "area": area, "attempts": 0, "makes": 0})
        t["attempts"] += z["attempts"]
        t["makes"] += z["makes"]

    league_lookup = {}
    if season:
        for row in LeagueZoneAverage.objects.filter(season=season).values("zone_basic", "zone_area", "attempts", "makes"):
            basic = row["zone_basic"]
            area = row["zone_area"] if basic in SPLIT_BASIC_ZONES else ""
            key = combined_zone_key(basic, area)
            t = league_lookup.setdefault(key, {"attempts": 0, "makes": 0})
            t["attempts"] += row["attempts"]
            t["makes"] += row["makes"]

    zone_stats = []
    for key, t in sorted(zone_totals.items(), key=lambda kv: -kv[1]["attempts"]):
        att = t["attempts"]
        mk = t["makes"]
        pct = round(100 * mk / att) if att else 0

        league_pct = None
        diff = None
        league_row = league_lookup.get(key)
        if league_row and league_row["attempts"] and att >= MIN_ZONE_ATTEMPTS_FOR_COMPARISON:
            league_pct = round(100 * league_row["makes"] / league_row["attempts"], 1)
            diff = round(pct - league_pct, 1)

        zone_stats.append({
            "zone": key,
            "zone_label": zone_display_label(t["basic"], t["area"]),
            "attempts": att,
            "makes": mk,
            "pct": pct,
            "league_pct": league_pct,
            "diff": diff,
        })

    season_pills = []
    for s in seasons:
        entry = {"value": s, "active": s == season}
        if url_for_season:
            entry["url"] = url_for_season(s)
        season_pills.append(entry)

    return {
        "total": total,
        "made": made,
        "fg_pct": round(100 * made / total) if total else 0,
        "shown_count": total,
        "seasons": seasons,
        "season_pills": season_pills,
        "active_season": season,
        "shot_types": shot_types,
        "active_type": shot_type,
        "shot_points": shot_points,
        "zone_stats": zone_stats,
    }
