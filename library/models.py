from django.db import models


class Player(models.Model):
    """A player we can attach film examples to. Thin for now — fleshed out when we wire nba_api."""
    name = models.CharField(max_length=100)
    nba_api_id = models.IntegerField(null=True, blank=True, unique=True)  # e.g. LeBron = 2544; nullable until we backfill
    team = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Action(models.Model):
    """A named basketball concept/action — the teaching spine. e.g. 'Pistol', 'Spain Pick and Roll'."""

    class Category(models.TextChoices):
        PICK_AND_ROLL = "PNR", "Pick and Roll"
        OFF_BALL = "OFF", "Off-Ball Screen"
        TRANSITION = "TRA", "Transition"
        POST = "POST", "Post-Up"
        ISOLATION = "ISO", "Isolation"
        OTHER = "OTH", "Other"

    class Difficulty(models.IntegerChoices):
        BEGINNER = 1, "Beginner"
        INTERMEDIATE = 2, "Intermediate"
        ADVANCED = 3, "Advanced"

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)  # for clean URLs: /actions/pistol/
    aliases = models.CharField(max_length=200, blank=True, help_text="Other names, comma-separated. e.g. '21 series, drag'")
    category = models.CharField(max_length=4, choices=Category.choices, default=Category.OTHER)
    difficulty = models.IntegerField(choices=Difficulty.choices, default=Difficulty.BEGINNER)
    breakdown = models.TextField(help_text="The written explanation of what happens in this action.")
    synergy_play_types = models.CharField(
        max_length=200, blank=True,
        help_text="Related nba_api Synergy play types, comma-separated. e.g. 'Handoff, PRBallHandler'"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Example(models.Model):
    """A single film example of an Action — an embedded, trimmed YouTube clip."""
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name="examples")
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="examples")
    title = models.CharField(max_length=200, help_text="e.g. 'LeBron pistol into stepback, 2024 vs BOS'")
    youtube_id = models.CharField(max_length=20, help_text="Just the ID, e.g. '-62TOKx8mfA' (the part after v=)")
    start_seconds = models.PositiveIntegerField(default=0, help_text="Clip start time in seconds.")
    end_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Clip end time in seconds. Leave blank to play to the end.")
    note = models.TextField(blank=True, help_text="What to watch for in this clip.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def embed_url(self):
        url = f"https://www.youtube.com/embed/{self.youtube_id}?start={self.start_seconds}"
        if self.end_seconds:
            url += f"&end={self.end_seconds}"
        return url