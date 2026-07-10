from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import Action, Player, Shot


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

    context = {
        "player": player,
        "shot_points": shot_points,
        "zone_stats": zone_stats,
        "total": total,
        "made": made,
        "fg_pct": round(100 * made / total) if total else 0,
        "seasons": seasons,
        "active_season": season,
        "shown_count": shots.count(),
    }
    return render(request, "library/player_detail.html", context)