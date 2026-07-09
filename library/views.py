# ============================================================
# library/views.py  —  ADD these to your existing views.
# (Keep your existing action_list and action_detail.)
# ============================================================

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import Action, Player, Shot


# --- existing action views stay as they are ---
def action_list(request):
    actions = Action.objects.filter(is_published=True).order_by("name")
    return render(request, "library/action_list.html", {"actions": actions})


def action_detail(request, slug):
    action = get_object_or_404(Action, slug=slug, is_published=True)
    return render(request, "library/action_detail.html", {"action": action})


# --- NEW: player views ---

def player_list(request):
    """Browsable index of players who have shot data."""
    players = (
        Player.objects
        .annotate(shot_count=Count("shots"))
        .filter(shot_count__gt=0)
        .order_by("name")
    )
    return render(request, "library/player_list.html", {"players": players})


def player_detail(request, pk):
    """A player's profile: shot chart (dots + zones) and shooting splits."""
    player = get_object_or_404(Player, pk=pk)
    shots = player.shots.all()

    total = shots.count()
    made = shots.filter(made=True).count()

    # Season filter (optional ?season=2023-24)
    season = request.GET.get("season")
    seasons = list(shots.values_list("season", flat=True).distinct().order_by("season"))
    if season and season in seasons:
        shots = shots.filter(season=season)

    # Build the plain shot list for the dot chart (small dicts, not model objects)
    shot_points = [
        {"x": s.loc_x, "y": s.loc_y, "made": s.made, "v": s.shot_value}
        for s in shots
    ]

    # Zone efficiency: bucket by SHOT_ZONE_BASIC, compute FG%
    zones = (
        shots.values("zone_basic")
        .annotate(
            attempts=Count("id"),
            makes=Count("id", filter=Q(made=True)),
        )
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