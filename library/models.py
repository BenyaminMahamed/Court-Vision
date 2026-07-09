from django.db import models
from django.urls import reverse


class Player(models.Model):
    @property
    def headshot_url(self):
        """Official NBA headshot, keyed by player id. Falls back to None if we have no id."""
        if not self.nba_api_id:
            return None
        return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{self.nba_api_id}.png"
    """A player we can attach film examples to. Thin for now — fleshed out when we wire nba_api."""
    name = models.CharField(max_length=100)
    nba_api_id = models.IntegerField(null=True, blank=True, unique=True)  # e.g. LeBron = 2544; nullable until we backfill
    team = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["name"]

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

    # --- Identity ---
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)  # clean URLs: /actions/pistol-action/
    aliases = models.CharField(
        max_length=200, blank=True,
        help_text="Other names, comma-separated. e.g. '21, drag'"
    )

    # --- Classification ---
    category = models.CharField(max_length=4, choices=Category.choices, default=Category.OTHER)
    difficulty = models.IntegerField(choices=Difficulty.choices, default=Difficulty.BEGINNER)

    # --- Variation structure (a variation/counter of a base action, e.g. Pistol Keep -> Pistol) ---
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="variations",
        help_text="If this is a variation or counter of a base action, link the base action here."
    )

    # --- Teaching content ---
    breakdown = models.TextField(help_text="The written explanation of what happens in this action.")
    key_reads = models.TextField(
        blank=True,
        help_text="Optional: the key reads or what to watch for, as a short list or paragraph."
    )

    # --- Stats bridge ---
    synergy_play_types = models.CharField(
        max_length=200, blank=True,
        help_text="Related nba_api Synergy play types, comma-separated. e.g. 'Handoff, PRBallHandler'"
    )

    # --- Housekeeping ---
    is_published = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this action from the public site while you work on it."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("library:action_detail", kwargs={"slug": self.slug})

    @property
    def play_type_list(self):
        """Split the comma-separated Synergy play types into a clean list for display."""
        if not self.synergy_play_types:
            return []
        return [pt.strip() for pt in self.synergy_play_types.split(",") if pt.strip()]

    @property
    def alias_list(self):
        """Split the comma-separated aliases into a clean list for display."""
        if not self.aliases:
            return []
        return [a.strip() for a in self.aliases.split(",") if a.strip()]


class Example(models.Model):
    """A single film example of an Action — a trimmed YouTube clip (link for now, embed later)."""
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name="examples")
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="examples")
    title = models.CharField(max_length=200, help_text="e.g. 'LeBron pistol into stepback, 2024 vs BOS'")
    youtube_id = models.CharField(max_length=20, help_text="Just the ID, e.g. '-62TOKx8mfA' (the part after v=)")
    start_seconds = models.PositiveIntegerField(default=0, help_text="Clip start time in seconds.")
    end_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Clip end time in seconds. Leave blank to play to the end.")
    note = models.TextField(blank=True, help_text="What to watch for in this clip.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.title

    @property
    def embed_url(self):
        url = f"https://www.youtube.com/embed/{self.youtube_id}?start={self.start_seconds}&rel=0&modestbranding=1&vq=hd1080"
        if self.end_seconds:
            url += f"&end={self.end_seconds}"
        return url

    @property
    def watch_url(self):
        """Timestamped watch link (used for the link-out until phase-2 on-site clips)."""
        return f"https://www.youtube.com/watch?v={self.youtube_id}&t={self.start_seconds}s"


class Shot(models.Model):
    """
    A single field-goal attempt, sourced from nba_api ShotChartDetail.
    Populated by a local/scheduled management command, never fetched live from Render.
    """
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="shots")

    # --- Identity / dedup keys ---
    game_id = models.CharField(max_length=20)
    game_event_id = models.IntegerField()          # pairs with game_id for VideoEvents clip lookup
    game_date = models.DateField(null=True, blank=True)
    season = models.CharField(max_length=9)        # e.g. "2023-24"
    team_id = models.BigIntegerField(null=True, blank=True)

    # --- Location (for the shot chart) ---
    loc_x = models.IntegerField()                  # tenths of a foot from hoop, x
    loc_y = models.IntegerField()                  # tenths of a foot from hoop, y
    shot_distance = models.IntegerField(null=True, blank=True)

    # --- Outcome ---
    made = models.BooleanField(default=False)      # from SHOT_MADE_FLAG
    shot_value = models.IntegerField(default=2)    # 2 or 3, derived from SHOT_TYPE

    # --- Type / classification (raw material for pull-up vs C&S later) ---
    action_type = models.CharField(max_length=60, blank=True)   # e.g. "Pullup Jump Shot"
    shot_type = models.CharField(max_length=20, blank=True)     # "2PT Field Goal" / "3PT Field Goal"
    zone_basic = models.CharField(max_length=40, blank=True)    # SHOT_ZONE_BASIC
    zone_range = models.CharField(max_length=40, blank=True)    # SHOT_ZONE_RANGE

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game_id", "game_event_id"], name="unique_shot_per_game_event")
        ]
        indexes = [
            models.Index(fields=["player", "season"]),
            models.Index(fields=["action_type"]),
        ]
        ordering = ["-game_date"]

    def __str__(self):
        result = "MAKE" if self.made else "MISS"
        return f"{self.player.name} {self.shot_value}PT {result} ({self.game_date})"

    @property
    def has_video(self):
        """We can attempt a VideoEvents clip lookup for any shot with a game/event id."""
        return bool(self.game_id and self.game_event_id is not None)