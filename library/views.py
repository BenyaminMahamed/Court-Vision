from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import Action, Player, Shot
from .shot_types import category_expression, CATEGORY_LABELS


def _url_with(request, **overrides):
    """Build '?a=1&b=2' preserving existing query params, applying overrides.
    Passing a value of None removes that param (used for 'clear this filter')."""
    params = request.GET.copy()
    for key, value in overrides.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    qs = params.urlencode()
    return f"?{qs}" if qs else "?"


# ---- Action views ----

def action_list(request):
    actions = Action.objects.filter(is_published=True).order_by("name")
    return render(request, "library/action_list.html", {"actions": actions})


def action_detail(request, slug):
    action = get_object_or_404(Action, slug=slug, is_published=True)
    return render(request, "library/action_detail.html", {"action": action})


# ---- Player views ----

def player_list(request):
    players = (
        Player.objects
        .annotate(shot_count=Count("shots"))
        .filter(shot_count__gt=0)
        .order_by("name")
    )
    return render(request, "library/player_list.html", {"players": players})


def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    shots = player.shots.all()

    total = shots.count()
    made = shots.filter(made=True).count()

    season = request.GET.get("season")
    seasons = list(shots.values_list("season", flat=True).distinct().order_by("season"))
    if season and season in seasons:
        shots = shots.filter(season=season)

    # Bucket every remaining shot (post season-filter) into a shot type once, up front.
    shots = shots.annotate(shot_category=category_expression())

    # Type counts reflect the season filter but NOT the type filter itself,
    # so switching between type pills doesn't make the other pills' counts vanish.
    type_counts = (
        shots.values("shot_category")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    shot_types = [
        {
            "key": row["shot_category"],
            "label": CATEGORY_LABELS.get(row["shot_category"], row["shot_category"]),
            "count": row["n"],
            "url": _url_with(request, type=row["shot_category"]),
            "active": row["shot_category"] == request.GET.get("type"),
        }
        for row in type_counts if row["n"] > 0
    ]
    valid_type_keys = {row["shot_category"] for row in type_counts}

    shot_type = request.GET.get("type")
    if shot_type and shot_type in valid_type_keys:
        shots = shots.filter(shot_category=shot_type)

    # Shot points for the chart — includes game/event/season for the NBA clip link
    shot_points = [
        {
            "x": s.loc_x, "y": s.loc_y, "made": s.made, "v": s.shot_value,
            "gid": s.game_id, "eid": s.game_event_id, "season": s.season,
        }
        for s in shots
    ]

    # Zone efficiency
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

    season_pills = [
        {"value": s, "url": _url_with(request, season=s), "active": s == season}
        for s in seasons
    ]

    context = {
        "player": player,
        "shot_points": shot_points,
        "zone_stats": zone_stats,
        "total": total,
        "made": made,
        "fg_pct": round(100 * made / total) if total else 0,
        "seasons": seasons,
        "season_pills": season_pills,
        "all_seasons_url": _url_with(request, season=None),
        "active_season": season,
        "shot_types": shot_types,
        "all_types_url": _url_with(request, type=None),
        "active_type": shot_type,
        "shown_count": shots.count(),
    }
    return render(request, "library/player_detail.html", context)