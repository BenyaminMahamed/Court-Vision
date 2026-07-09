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

# ============================================================
# ADD to library/views.py (append these imports + views).
# Keep everything already in the file.
# ============================================================

import requests
from django.http import StreamingHttpResponse, HttpResponse, JsonResponse

# nba.com CDN needs this referer or it returns "video not available"
NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.nba.com/",
}


def _get_clip_url(game_id, event_id):
    """Resolve a shot's game/event to an HD .mp4 URL via VideoEvents. Returns url or None."""
    try:
        from nba_api.stats.endpoints import videoeventsasset
    except ImportError:
        return None
    try:
        va = videoeventsasset.VideoEventsAsset(
            game_id=str(game_id), game_event_id=int(event_id), timeout=20,
        )
        urls = va.get_dict()["resultSets"]["Meta"]["videoUrls"]
        if urls and urls[0].get("lurl"):
            return urls[0]["lurl"]
    except Exception:
        return None
    return None


def clip_test(request, game_id, event_id):
    """
    DIAGNOSTIC: does Render's server reach videos.nba.com?
    Visit /clip-test/<game_id>/<event_id>/ and read the JSON it returns.
    Remove this view once we know the answer.
    """
    result = {"game_id": game_id, "event_id": event_id}

    # Step 1: can we even resolve the clip URL from here? (this hits stats.nba.com)
    clip_url = _get_clip_url(game_id, event_id)
    result["videoevents_resolved"] = bool(clip_url)
    result["clip_url"] = clip_url

    if not clip_url:
        result["verdict"] = "Could NOT resolve clip URL — stats.nba.com likely blocked from Render."
        return JsonResponse(result, json_dumps_params={"indent": 2})

    # Step 2: can we fetch the actual .mp4 with the referer header?
    try:
        r = requests.get(clip_url, headers=NBA_HEADERS, stream=True, timeout=25)
        result["mp4_status_code"] = r.status_code
        result["mp4_content_type"] = r.headers.get("Content-Type")
        result["mp4_content_length"] = r.headers.get("Content-Length")
        r.close()
        if r.status_code == 200 and "video" in (r.headers.get("Content-Type") or ""):
            result["verdict"] = "SUCCESS — Render can fetch the clip. Proxy will work."
        else:
            result["verdict"] = f"Fetched but not a video (status {r.status_code}). CDN may gate Render."
    except Exception as e:
        result["mp4_error"] = str(e)
        result["verdict"] = "FAILED to fetch mp4 from Render — CDN likely blocks Render's IP."

    return JsonResponse(result, json_dumps_params={"indent": 2})


def clip_stream(request, game_id, event_id):
    """
    REAL PROXY: fetch the clip server-side (with referer) and stream it to the browser.
    The <video> tag points here, so the browser never talks to nba.com directly.
    """
    clip_url = _get_clip_url(game_id, event_id)
    if not clip_url:
        return HttpResponse("Clip not available.", status=404)

    try:
        upstream = requests.get(clip_url, headers=NBA_HEADERS, stream=True, timeout=25)
    except Exception:
        return HttpResponse("Upstream fetch failed.", status=502)

    if upstream.status_code != 200:
        return HttpResponse("Clip not available.", status=upstream.status_code)

    resp = StreamingHttpResponse(
        upstream.iter_content(chunk_size=64 * 1024),
        content_type=upstream.headers.get("Content-Type", "video/mp4"),
    )
    if upstream.headers.get("Content-Length"):
        resp["Content-Length"] = upstream.headers["Content-Length"]
    resp["Accept-Ranges"] = "bytes"
    return resp