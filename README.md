# Court Vision

**Learn to read the game.** A free basketball film-study tool: a searchable library of named actions (pistol, Spain pick-and-roll, horns) with written breakdowns, plus interactive player shot charts where every shot links to its own game film.

**Live:** https://court-vision-ng9w.onrender.com

Court Vision exists to solve a specific problem: when you start studying basketball film, you see actions happening but can't name them — and there's no single place to look one up, understand it, and watch how it plays out. Stats sites give you numbers with no film. Film tools like Synergy are paywalled and coach-facing. Court Vision sits in the gap: a free, concept-indexed tool built for people learning to watch the game.

## Status

Live and in active development. Shipped: the **action library** (a scouting-report-style glossary of basketball concepts) and **player shot charts** — interactive charts and zone splits from real NBA shot data, where clicking any shot opens that exact possession on NBA.com.

## Features

### Action library
- Each action has a written breakdown, key reads, category, difficulty, alternate names, and related Synergy play types, on its own clean URL (e.g. `/actions/pistol-action/`).
- Presented as a structured scouting report: classification tags, breakdown, key reads, related play types, and film examples.
- Authored through the Django admin, with film examples editable inline.
- Supports linking variations to a base action (e.g. Pistol Keep to Pistol) and a publish flag for drafting privately.

### Player shot charts
- Browsable player index and per-player profiles with official headshots and shooting summary stats.
- Interactive SVG shot chart rendered from real NBA shot coordinates — makes and misses plotted to scale, with a season filter.
- **Every shot is clickable and opens that exact possession's video on NBA.com** — turning the shot chart into a portal to game film.
- Zone-by-zone shooting splits (FG% by court area) computed from the shot data.
- Populated by a local, resumable management command that pulls shot data via `nba_api`, ranks players by shot volume, and caches results into PostgreSQL.

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
- **Shot** — a single field-goal attempt (player, game/event ids, location, make/miss, value, shot type, zone), unique per game event, indexed for chart and split queries. The stored game and event ids also build the direct NBA.com video link for each shot.

## Data pipeline

NBA shot data is not fetched at request time — `stats.nba.com` rate-limits and blocks datacenter IPs, so ingestion runs from a local machine, not the deployed server. A management command (`import_season`) pulls a season's players ranked by shot volume, fetches each player's shots from `nba_api`, and caches them into PostgreSQL. It is idempotent and resumable: safe to re-run after a timeout, skipping already-imported players. The deployed app only ever reads from PostgreSQL.

The shot-to-film link needs no caching: each shot's stored game id, event id, and season construct a direct NBA.com URL that plays that exact possession in NBA's own player.

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

Visit `/` for the library, `/players/` for shot charts, `/admin/` to add content.

Import shot data locally (writes to whatever `DATABASE_URL` points at):

```bash
python manage.py import_season --season 2025-26 --limit 50
python manage.py backfill_teams --season 2025-26
```

## Roadmap

1. **Shot-type filtering** — filter a player's shots (and their clips) by type, e.g. pull-up vs. catch-and-shoot.
2. **League-relative splits** — compare a player's zone efficiency to league average to surface strengths and weaknesses.
3. **Zone overlay** — a colored zone view on the shot chart alongside the dot view.
4. **More action content** — expand the library across more actions and variations.
5. **Play-style recommendation** — a diagnostic quiz mapping answers to play-style axes and recommending actions and players to study.

## A note on data and media

Court Vision indexes and links rather than rehosting. Shot data and headshots are drawn from official NBA sources, and shot clips open on NBA.com in NBA's own player — the app never hosts or rehosts video.

## License

MIT — see [LICENSE](LICENSE).
