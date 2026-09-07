from django.contrib import admin
from .models import Player, Action, Example, LeagueZoneAverage


class ExampleInline(admin.TabularInline):
    """Lets you add film examples directly on the Action page."""
    model = Example
    extra = 1


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "difficulty", "created_at")
    list_filter = ("category", "difficulty")
    search_fields = ("name", "aliases")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ExampleInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "nba_api_id")
    search_fields = ("name",)


@admin.register(Example)
class ExampleAdmin(admin.ModelAdmin):
    list_display = ("title", "action", "player", "youtube_id")
    list_filter = ("action",)
    search_fields = ("title", "note")


@admin.register(LeagueZoneAverage)
class LeagueZoneAverageAdmin(admin.ModelAdmin):
    list_display = ("season", "zone_basic", "pct", "makes", "attempts")
    list_filter = ("season",)
