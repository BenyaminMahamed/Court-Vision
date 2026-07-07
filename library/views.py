from django.shortcuts import render, get_object_or_404
from .models import Action


def action_list(request):
    actions = Action.objects.all().order_by("name")
    return render(request, "library/action_list.html", {"actions": actions})


def action_detail(request, slug):
    action = get_object_or_404(Action, slug=slug)
    return render(request, "library/action_detail.html", {"action": action})