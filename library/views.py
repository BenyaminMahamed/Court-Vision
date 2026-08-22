from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Action, Player, Shot
from .queries import get_player_shot_data


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

    season = request.GET.get("season")
    shot_type = request.GET.get("type")
    shots, meta = get_player_shot_data(player, season=season, shot_type=shot_type)

    # Shot points for the chart — includes game/event/season for the NBA clip link
    shot_points = [
        {
            "x": s.loc_x, "y": s.loc_y, "made": s.made, "v": s.shot_value,
            "gid": s.game_id, "eid": s.game_event_id, "season": s.season,
        }
        for s in shots
    ]

    season_pills = [
        {"value": s, "url": _url_with(request, season=s), "active": s == season}
        for s in meta["seasons"]
    ]
    shot_type_pills = [
        {
            "key": t["key"], "label": t["label"], "count": t["count"],
            "url": _url_with(request, type=t["key"]), "active": t["key"] == shot_type,
        }
        for t in meta["shot_types"]
    ]

    context = {
        "player": player,
        "shot_points": shot_points,
        "zone_stats": meta["zone_stats"],
        "total": meta["total"],
        "made": meta["made"],
        "fg_pct": meta["fg_pct"],
        "seasons": meta["seasons"],
        "season_pills": season_pills,
        "all_seasons_url": _url_with(request, season=None),
        "active_season": season,
        "shot_types": shot_type_pills,
        "all_types_url": _url_with(request, type=None),
        "active_type": shot_type,
        "shown_count": meta["total"],
    }
    return render(request, "library/player_detail.html", context)


def player_compare(request):
    players = (
        Player.objects
        .annotate(shot_count=Count("shots"))
        .filter(shot_count__gt=0)
        .order_by("name")
    )
    context = {
        "players": players,
        "initial_a": request.GET.get("a", ""),
        "initial_b": request.GET.get("b", ""),
    }
    return render(request, "library/player_compare.html", context)