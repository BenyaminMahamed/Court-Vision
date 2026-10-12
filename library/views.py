from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import Action, Player, Shot
from .queries import get_player_shot_data
from .shot_types import category_expression, CATEGORY_LABELS
from .quiz_data import QUIZ_QUESTIONS, quiz_result


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
    season = request.GET.get("season")
    seasons = list(Shot.objects.values_list("season", flat=True).distinct().order_by("season"))

    shot_count_filter = Q(shots__season=season) if season and season in seasons else Q()
    players = (
        Player.objects
        .annotate(shot_count=Count("shots", filter=shot_count_filter))
        .filter(shot_count__gt=0)
        .order_by("name")
    )

    season_pills = [
        {"value": s, "url": _url_with(request, season=s), "active": s == season}
        for s in seasons
    ]

    context = {
        "players": players,
        "seasons": seasons,
        "season_pills": season_pills,
        "active_season": season,
        "all_seasons_url": _url_with(request, season=None),
    }
    return render(request, "library/player_list.html", context)


def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)

    season = request.GET.get("season")
    shot_type = request.GET.get("type")

    data = get_player_shot_data(
        player,
        season=season,
        shot_type=shot_type,
        url_for_season=lambda s: _url_with(request, season=s),
        url_for_type=lambda t: _url_with(request, type=t),
    )

    context = {
        "player": player,
        **data,
        "all_seasons_url": _url_with(request, season=None),
        "all_types_url": _url_with(request, type=None),
    }
    return render(request, "library/player_detail.html", context)


def player_compare(request):
    players = (
        Player.objects
        .annotate(shot_count=Count("shots"))
        .filter(shot_count__gt=0)
        .order_by("name")
    )
    seasons = list(Shot.objects.values_list("season", flat=True).distinct().order_by("season"))
    context = {
        "players": players,
        "seasons": seasons,
        "initial_a": request.GET.get("a", ""),
        "initial_b": request.GET.get("b", ""),
        "initial_season": request.GET.get("season", ""),
    }
    return render(request, "library/player_compare.html", context)


def play_style_quiz(request):
    """
    GET: show the quiz.
    POST: score the answers into a primary+secondary archetype (see
    quiz_data.quiz_result), recommend an Action category, and surface the
    real players in the dataset whose BEST SINGLE SEASON in the primary
    category is strongest -- each player is credited for their peak year,
    not an average blended across every season on file. So if a player
    shot much better from a zone in 2024-25 than 2025-26, their 2024-25
    number is what gets them ranked, and that season is shown alongside
    their name.
    """
    MIN_SHOTS_PER_SEASON = 50

    if request.method == "POST":
        answers = {
            q["id"]: request.POST.get(q["id"])
            for q in QUIZ_QUESTIONS
            if request.POST.get(q["id"])
        }
        if len(answers) < len(QUIZ_QUESTIONS):
            context = {
                "questions": QUIZ_QUESTIONS,
                "error": "Answer every question to get your result.",
            }
            return render(request, "library/play_style_quiz.html", context)

        result = quiz_result(answers)
        category = result["primary"]

        recommended_actions = (
            Action.objects
            .filter(is_published=True, category=result["action_category"])
            .order_by("difficulty", "name")[:3]
        )

        season_category_counts = (
            Shot.objects
            .annotate(shot_category=category_expression())
            .values("player_id", "season")
            .annotate(
                total=Count("id"),
                in_category=Count("id", filter=Q(shot_category=category)),
            )
            .filter(total__gte=MIN_SHOTS_PER_SEASON)
        )

        best_per_player = {}
        for row in season_category_counts:
            pct = row["in_category"] / row["total"]
            pid = row["player_id"]
            best = best_per_player.get(pid)
            if best is None or pct > best["pct"]:
                best_per_player[pid] = {
                    "player_id": pid,
                    "season": row["season"],
                    "pct": pct,
                    "attempts": row["total"],
                }

        ranked = sorted(best_per_player.values(), key=lambda row: -row["pct"])[:5]

        players_by_id = Player.objects.in_bulk([row["player_id"] for row in ranked])
        top_players = [
            {
                "player": players_by_id[row["player_id"]],
                "season": row["season"],
                "pct": round(100 * row["pct"]),
                "attempts": row["attempts"],
            }
            for row in ranked
            if row["player_id"] in players_by_id
        ]

        total_answers = sum(result["scores"].values())
        breakdown = sorted(
            [
                {
                    "key": key,
                    "label": CATEGORY_LABELS[key],
                    "pct": round(100 * count / total_answers) if total_answers else 0,
                }
                for key, count in result["scores"].items()
            ],
            key=lambda row: -row["pct"],
        )

        context = {
            "result": result,
            "breakdown": breakdown,
            "recommended_actions": recommended_actions,
            "top_players": top_players,
        }
        return render(request, "library/play_style_quiz.html", context)

    context = {"questions": QUIZ_QUESTIONS}
    return render(request, "library/play_style_quiz.html", context)
