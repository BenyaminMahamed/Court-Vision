# Court Vision

**Learn to read the game.** A free basketball film-study tool: a searchable library of named actions (pistol, Spain pick-and-roll, horns) with written breakdowns, plus player shot charts and shooting splits pulled from real NBA data.

**Live:** https://court-vision-ng9w.onrender.com

Court Vision exists to solve a specific problem: when you start studying basketball film, you see actions happening but can't name them — and there's no single place to look one up, understand it, and see how it plays out. Stats sites give you numbers with no context. Film tools like Synergy are paywalled and coach-facing. Court Vision sits in the gap: a free, concept-indexed tool built for people learning to watch the game.

## Status

Live and in active development. Two features are shipped: the **action library** (a scouting-report-style glossary of basketball concepts) and **player shot charts** (interactive charts and zone shooting splits built from real NBA shot data). On-site film clips and shot-type search are next (see Roadmap).

## Features

### Action library
- Each action has a written breakdown, key reads, category, difficulty, alternate names, and related Synergy play types, served on its own clean URL (e.g. `/actions/pistol-action/`).
- Presented as a structured scouting report: classification tags, breakdown, key reads, related play types, and film examples.
- Authored through the Django admin, with film examples editable inline on each action.
- Supports linking variations and counters to a base action (e.g. Pistol Keep to Pistol) and a publish flag to draft actions privately.

### Player shot charts
- Browsable player index and per-player profile pages with official headshots.
- Interactive SVG shot chart rendered from real NBA shot coordinates — makes and misses plotted to scale on the court, with a dots/zones toggle and season filter.
- Zone-by-zone shooting splits (FG% by court area) computed from the shot data.
- Populated by a local, resumable management command that pulls shot data via `nba_api`, ranks players by shot volume, and caches results into PostgreSQL — the app never calls the NBA API at request time.

## Tech stack

- **Backend:** Python, Django
- **Database:** PostgreSQL (Neon) in production, SQLite in local development
- **Frontend:** Django templates with vanilla JS and inline SVG, server-rendered (no build pipeline)
- **Hosting:** Render (web service) + Neon (managed Postgres)
- **Data:** the `nba_api` package for shot-chart data, ingested via a local management command

## Data model

- **Action** — a named basketball concept (name, slug, aliases, category, difficulty, optional parent action for variations, breakdown, key reads, related Synergy play types, publish flag).
- **Example** — a film example of an action (title, YouTube video ID, start/end seconds, note, optional player).
- **Player** — an NBA player (name, team, NBA API id) with a derived headshot URL.
- **Shot** — a single field-goal attempt (player, game/event ids, location, make/miss, value, shot type, zone), unique per game event, indexed for chart and split queries.

## Data pipeline

NBA shot data is not fetched live. A local management command (`import_season`) pulls a season's players ranked by shot volume, fetches each player's shots from `nba_api`, and caches them into PostgreSQL. The command is idempotent and resumable — safe to re-run after a timeout, skipping already-imported players — because `stats.nba.com` rate-limits and blocks datacenter IPs, so ingestion runs from a local machine rather than the deployed server.

## Running locally

```bash
# clone and enter the repo
git clone https://github.com/BenyaminMahamed/Court-Vision.git
cd Court-Vision

# create and activate a virtual environment
py -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# install dependencies
python -m pip install -r requirements.txt

# set up local environment variables
# create a .env file in the project root containing:
#   SECRET_KEY=your-local-key
#   DEBUG=True

# apply migrations and create an admin user
python manage.py migrate
python manage.py createsuperuser

# run the development server
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/` for the library, `http://127.0.0.1:8000/players/` for shot charts, and `http://127.0.0.1:8000/admin/` to add content.

To import shot data locally:

```bash
python manage.py import_season --season 2025-26 --limit 50
```

## Roadmap

Planned in rough order:

1. **On-site film clips** — serve possession-length clips through the NBA `VideoEvents` endpoint (proven viable), replacing external links with an on-site player.
2. **Shot-type search** — filter a player's shots by type (e.g. catch-and-shoot vs. off-the-dribble) and surface the matching clips.
3. **League-relative splits** — compare a player's zone efficiency to league average to show strengths and weaknesses at a glance.
4. **More action content** — expand the library across more actions and their variations (horns, zoom, off-ball series).
5. **Play-style recommendation** — a diagnostic quiz that maps a user's answers to play-style axes and recommends actions and players to study.

## A note on data and media

Court Vision indexes and links rather than rehosting. Film examples link to their original sources; player headshots and shot data are drawn from official NBA sources. The planned clip pipeline serves official NBA-hosted possession clips rather than rehosting footage.

## License

MIT — see [LICENSE](LICENSE).
