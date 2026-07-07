from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.action_list, name="action_list"),
    path("actions/<slug:slug>/", views.action_detail, name="action_detail"),
]