# Court Vision

**Learn to read the game.** A free, searchable library of basketball actions that maps named concepts (pistol, Spain pick-and-roll, horns) to written breakdowns and film examples.

**Live:** https://court-vision-ng9w.onrender.com

Court Vision exists to solve a specific problem: when you start studying basketball film, you see actions happening but can't name them — and there's no single place to look one up, understand it, and watch a clean example. Stats sites give you numbers with no film. Film tools like Synergy are paywalled and coach-facing. Court Vision sits in the gap: a concept-indexed film library that's free and built for people learning to watch the game.

## Status

Live and in active development. The core glossary — content model, admin-driven content management, public pages, and a courtside-styled interface — is deployed. A player-search feature backed by NBA play-by-play data is in progress (see Roadmap).

## Features

- **Action library** — each action has a written breakdown, category, difficulty, alternate names, and related Synergy play types, served on its own clean URL (e.g. `/actions/pistol-action/`).
- **Scouting-report pages** — each action is presented as a structured report: classification tags, breakdown, related play types, and film examples.
- **Admin-driven content** — actions and film examples are authored through the Django admin, with examples editable inline on each action.
- **Action variations** — the model supports linking variations and counters to a base action (e.g. Pistol Keep to Pistol).
- **Trimmed film examples** — examples reference a YouTube clip with a start and end time, so a viewer is pointed to the relevant possession rather than a full video.
- **Play-type bridge** — each action links to the relevant NBA Synergy play types (e.g. Handoff, PRBallHandler), keeping the teaching taxonomy separate from the stats taxonomy while allowing them to connect.

## Tech stack

- **Backend:** Python, Django
- **Database:** PostgreSQL (Neon) in production, SQLite in local development
- **Frontend:** Django templates, server-rendered (no build pipeline)
- **Hosting:** Render (web service) + Neon (managed Postgres)
- **Data source (in progress):** the `nba_api` package for Synergy play-type stats and play-by-play video data

## Data model

Three core models form the spine:

- **Action** — a named basketball concept (name, slug, aliases, category, difficulty, optional parent action for variations, written breakdown, key reads, related Synergy play types, publish flag).
- **Example** — a film example of an action (title, YouTube video ID, start/end seconds, note, optional player).
- **Player** — a player record (name, team, NBA API id) to be expanded when stats features are built.

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

Then visit `http://127.0.0.1:8000/` for the library and `http://127.0.0.1:8000/admin/` to add content.

## Roadmap

Planned in rough order:

1. **Action content** — expand the library across more actions (horns, zoom, off-ball series, and variations).
2. **Player stats** — surface NBA Synergy play-type stats on action and player pages via a scheduled job that caches data into PostgreSQL.
3. **On-site film clips** — serve possession-length clips through the NBA `VideoEvents` pipeline (proven viable), replacing external links with an on-site player.
4. **Player search** — let users find possessions by player and shot type (e.g. catch-and-shoot vs. off-the-dribble), backed by NBA play-by-play data.
5. **Play-style recommendation** — a diagnostic quiz that maps a user's answers to play-style axes and recommends relevant actions and players to study.

## A note on video

Court Vision indexes film; it does not host it. Film examples are linked from their original sources. The planned clip pipeline serves official NBA-hosted possession clips rather than rehosting any footage.

## License

MIT — see [LICENSE](LICENSE).
