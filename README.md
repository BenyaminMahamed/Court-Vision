# Court Vision

**Learn to read the game.** A free basketball film-study tool: a searchable library of named actions (pistol, Spain pick-and-roll, horns) with written breakdowns, interactive player shot charts where every shot links to its own game film, and head-to-head player comparison.

**Live:** https://court-vision-ng9w.onrender.com

Court Vision exists to solve a specific problem: when you start studying basketball film, you see actions happening but can't name them — and there's no single place to look one up, understand it, and watch how it plays out. Stats sites give you numbers with no film. Film tools like Synergy are paywalled and coach-facing. Court Vision sits in the gap: a free, concept-indexed tool built for people learning to watch the game.

## Status

Live and in active development. Shipped: the **action library** (a scouting-report-style glossary of basketball concepts across five categories: Pick and Roll, Off-Ball Screen, Transition, Post-Up, and Isolation), **player shot charts** with shot-type filtering, and **head-to-head player comparison**.

## Features

### Action library
- Each action has a written breakdown, key reads, category, difficulty, alternate names, and related Synergy play types, on its own clean URL (e.g. `/actions/pistol-action/`).
- Presented as a structured scouting report: classification tags, breakdown, key reads, related play types, and film examples.
- Authored through the Django admin, with film examples editable inline.
- Supports linking variations to a base action (e.g. Pistol Keep to Pistol) and a publish flag for drafting privately.
- 12 actions live, spanning five categories.

### Player shot charts
- Browsable index of 50 players (2025–26 season) with official headshots and shooting summary stats.
- Interactive SVG shot chart rendered from real NBA shot coordinates — makes and misses plotted to scale, with a season filter.
- **Shot-type filtering** — narrow the chart and zone splits by shot type (Pull-Up, Catch & Shoot, At the Rim, Post & Turnaround), bucketed from each shot's stored `action_type`.
- **Every shot is clickable and opens that exact possession's video on NBA.com** — turning the shot chart into a portal to game film.
- Zone-by-zone shooting splits (FG% by court area) computed from the shot data, respecting whatever season/type filters are active.
- Populated by a local, resumable management command that pulls shot data via `nba_api`, ranks players by shot volume, and caches results into PostgreSQL.

### Head-to-head comparison
- Select any two of the 50 tracked players for a side-by-side shot chart and zone breakdown.
- Compares total shots, FG%, and makes for each player, with a zone-by-zone head-to-head table (bolding whichever player shoots better from each zone).

## Tech stack

- **Backend:** Python, Django
- **Database:** PostgreSQL (Neon) in production, SQLite in local development
- **Frontend:** Django templates with vanilla JS and inline SVG, server-rendered (no build pipeline)
- **Hosting:** Render (web service) + Neon (managed Postgres)
- **Data:** the `nba_api` package for shot-chart data, ingested via local management commands

## Data model

- **Action** — a named basketball concept (name, slug, aliases, category, difficulty, optional parent action, breakdown, key reads, Synergy play types, publish flag).
- **Example** — a film example of an action (title, YouTube video ID, start/end seconds, note, optional player).
- **Player** — an NBA player (name, team, NBA API id) with a derived headshot URL.
- **Shot** — a single field-goal attempt (player, game/event ids, location, make/miss, value, shot type, action type, zone), unique per game event, indexed for chart, split, and shot-type-filter queries. The stored game and event ids also build the direct NBA.com video link for each shot.

## Data pipeline

NBA shot data is not fetched at request time — `stats.nba.com` rate-limits and blocks datacenter IPs, so ingestion runs from a local machine, not the deployed server. A management command (`import_season`) pulls a season's players ranked by shot volume, fetches each player's shots from `nba_api`, and caches them into PostgreSQL. It is idempotent and resumable: safe to re-run after a timeout, skipping already-imported players. The deployed app only ever reads from PostgreSQL.

The shot-to-film link needs no caching: each shot's stored game id, event id, and season construct a direct NBA.com URL that plays that exact possession in NBA's own player.

Shot-type filtering (Pull-Up, Catch & Shoot, At the Rim, Post & Turnaround) is computed from each shot's stored `action_type` field via a single SQL `Case` expression (`library/shot_types.py`), used both to filter and to count — so filtering and the displayed counts can never drift out of sync.

## Running locally

```bash
git clone https://github.com/BenyaminMahamed/Court-Vision.git
cd Court-Vision

py -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

python -m pip install -r requirements.txt

# create a .env in the project root with:
#   SECRET_KEY=your-local-key
#   DEBUG=True

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `/` for the library, `/players/` for shot charts, `/players/compare/` for head-to-head comparison, `/admin/` to add content.

Import shot data locally (writes to whatever `DATABASE_URL` points at):

```bash
python manage.py import_season --season 2025-26 --limit 50
python manage.py backfill_teams --season 2025-26
```

## In Progress: Computer Vision Shot-Accuracy Subsystem

A separate, standalone subsystem (`vision/`, isolated from the Django app — no integration yet) aimed at a "shot accuracy" feature: upload a game clip, detect the basketball/rim/backboard, track the ball's trajectory, and calculate how far off-center it crossed the rim plane on a shot attempt — conceptually similar to pitch-command tracking in baseball (target vs. actual location), adapted to basketball.

Calibration is anchored to the rim rather than court lines: rim height (10ft) and diameter (18in) are standardized across NBA, FIBA, and most levels, while court dimensions — the three-point line distance especially — vary. Anchoring to the rim is intended to let this generalize to footage from any court, not just a fixed camera setup.

**Data and training so far:**
- Baseline test with stock pretrained YOLOv8n (COCO weights, no fine-tuning) found zero basketballs across 15 sampled frames from three test clips — confirming custom training was necessary, not optional.
- Labeled 640 frames (basketball, rim, backboard classes) across two of the three clips using Roboflow's SAM3-based auto-labeler, 512/64/64 train/validation/test split, 640×640 letterboxed export.
- Fine-tuned YOLOv8n (from COCO-pretrained weights) locally on an NVIDIA RTX 4070 Laptop GPU, 50 epochs with early stopping. Training required a Python 3.11 environment — Python 3.13 caused an unresolved silent crash in the torch/ultralytics/CUDA stack.

**Current results:**
- Backboard detection: precision 0.93, recall 0.71, mAP50 0.885.
- Basketball detection: precision 0.75, recall 0.50, mAP50 0.516 — a large improvement on the zero-detection baseline, but still misses roughly half of real balls in validation.
- A recurring false-positive basketball detection appears across multiple different clips and venues, ruling out a specific background object as the cause. Current working theory is an artifact of the 640×640 letterbox padding; mitigated for now with a 0.7 confidence threshold at inference time while the root cause is investigated.
- Tested against a held-out clip (excluded from training entirely, different camera/venue) and correctly detected real basketballs in several frames — an encouraging generalization signal beyond the raw validation numbers.

**Not yet built:** improving basketball detection recall, resolving an observed backboard hoop-side inconsistency, the actual rim-crossing/trajectory math, and Django integration (deliberately last, once the CV pipeline works standalone).

## Roadmap

1. **Film examples for the action library** — source and attach real film clips (YouTube ID + timestamp) for every action, especially the newer additions.
2. **League-relative splits** — compare a player's zone efficiency to league average to surface strengths and weaknesses.
3. **Zone overlay** — a colored zone view on the shot chart alongside the dot view.
4. **In-page clip playback** — play shot clips directly on the site instead of linking out to NBA.com, filterable by the same shot types as the chart (currently: "Film coming soon" on player profile pages).
5. **Play-style recommendation** — a diagnostic quiz mapping answers to play-style axes and recommending actions and players to study.

## A note on data and media

Court Vision indexes and links rather than rehosting. Shot data and headshots are drawn from official NBA sources, and shot clips open on NBA.com in NBA's own player — the app never hosts or rehosts video.

## License

MIT — see [LICENSE](LICENSE).
