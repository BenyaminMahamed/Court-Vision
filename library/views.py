from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import Action, Player, Shot
from .queries import get_player_shot_data
from .shot_types import category_expression
from .quiz_data import QUIZ_QUESTIONS, PLAYSTYLE_RESULTS, score_quiz


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
    context = {
        "players": players,
        "initial_a": request.GET.get("a", ""),
        "initial_b": request.GET.get("b", ""),
    }
    return render(request, "library/player_compare.html", context)


def play_style_quiz(request):
    """
    GET: show the quiz.
    POST: score the answers and recommend an Action category plus the real
    players in the dataset whose actual shot mix leans hardest into the
    resulting playstyle -- computed live from Shot data via the same
    category_expression() shot_types.py already uses, not hardcoded.
    """
    MIN_SHOTS_FOR_RECOMMENDATION = 150

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
                "answers": answers,
            }
            return render(request, "library/play_style_quiz.html", context)

        category = score_quiz(answers)
        result = PLAYSTYLE_RESULTS[category]

        recommended_actions = (
            Action.objects
            .filter(is_published=True, category=result["action_category"])
            .order_by("difficulty", "name")[:3]
        )

        category_counts = (
            Shot.objects
            .annotate(shot_category=category_expression())
            .values("player_id")
            .annotate(
                total=Count("id"),
                in_category=Count("id", filter=Q(shot_category=category)),
            )
            .filter(total__gte=MIN_SHOTS_FOR_RECOMMENDATION)
        )

        ranked = sorted(
            category_counts,
            key=lambda row: row["in_category"] / row["total"],
            reverse=True,
        )[:5]

        players_by_id = Player.objects.in_bulk([row["player_id"] for row in ranked])
        top_players = [
            {
                "player": players_by_id[row["player_id"]],
                "pct": round(100 * row["in_category"] / row["total"]),
                "attempts": row["total"],
            }
            for row in ranked
            if row["player_id"] in players_by_id
        ]

        context = {
            "result": result,
            "category": category,
            "recommended_actions": recommended_actions,
            "top_players": top_players,
        }
        return render(request, "library/play_style_quiz.html", context)

    context = {"questions": QUIZ_QUESTIONS}
    return render(request, "library/play_style_quiz.html", context)
