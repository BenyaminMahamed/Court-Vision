"""
Shared shot-query layer for player shot data.

Single source of truth for turning a Player + season/type filters into
totals, zone splits, and a plotted shot list. Both the HTML player_detail
view and the shotchart API call get_player_shot_data(), so there is
exactly one place this math happens — not two copies that can quietly
drift apart.

Bug fixed by this extraction: the old player_detail view computed
made/fg_pct from the player's *entire* shot history, while shown_count
respected whatever season/type filter was active. So filtering to one
season updated the shot count but silently left "Field Goal %" and
"Made" showing career-wide numbers. Every value returned below is now
computed from the same, fully-filtered queryset — total, made, fg_pct,
and shown_count can never disagree again.
"""
from django.db.models import Count, Q

from .shot_types import category_expression, CATEGORY_LABELS


def get_player_shot_data(player, season=None, shot_type=None, url_for_season=None, url_for_type=None):
    """
    Returns a dict of everything a shot chart needs for `player`, filtered
    by `season` and `shot_type` if given and valid:

        total, made, fg_pct, shown_count,
        seasons, season_pills, active_season,
        shot_types, active_type,
        shot_points, zone_stats

    `url_for_season` / `url_for_type` are optional callables (key) -> url
    used to build filter-pill links for the HTML page. The API doesn't
    need pill links, so it just omits them.
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

    zones = (
        shots.values("zone_basic")
        .annotate(attempts=Count("id"), makes=Count("id", filter=Q(made=True)))
        .order_by("-attempts")
    )
    zone_stats = []
    for z in zones:
        if not z["zone_basic"]:
            continue
        att = z["attempts"]
        mk = z["makes"]
        zone_stats.append({
            "zone": z["zone_basic"],
            "attempts": att,
            "makes": mk,
            "pct": round(100 * mk / att) if att else 0,
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
