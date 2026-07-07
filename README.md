# Court Vision

**Learn to read the game.** A free, searchable library of basketball actions that maps named concepts (pistol, Spain pick-and-roll, horns) to written breakdowns and trimmed film examples.

Court Vision exists to solve a specific problem: when you start studying basketball film, you see actions happening but can't name them — and there's no single place to look one up, understand it, and watch a clean example. Stats sites give you numbers with no film. Film tools like Synergy are paywalled and coach-facing. Court Vision aims to sit in the gap: a concept-indexed film library that's free and built for people learning to watch the game.

## Status

Working MVP, features in progress. The core glossary — content model, admin-driven content management, public pages, and trimmed video embeds — is functional and deployable. Player search and a play-style recommendation layer are planned (see Roadmap).

## Features

- **Action library** — each action has a written breakdown, category, difficulty, and alternate names, served on its own clean URL (e.g. `/actions/pistol-action/`).
- **Admin-driven content** — actions and film examples are authored through the Django admin, with film examples editable inline on each action.
- **Trimmed film embeds** — examples embed a YouTube clip trimmed to a specific start and end time, so a viewer sees the relevant possession rather than a full video.
- **Play-type bridge** — each action links to the relevant NBA Synergy play types (e.g. Handoff, PRBallHandler), keeping the teaching taxonomy separate from the stats taxonomy while allowing them to connect for planned stats features.

## Tech stack

- **Backend:** Python, Django
- **Database:** PostgreSQL (production), SQLite (local development)
- **Frontend:** Django templates with HTMX and vanilla JavaScript (server-rendered, no build pipeline)
- **Planned data source:** the `nba_api` package for Synergy play-type stats and play-by-play data

## Data model

Three core models form the spine:

- **Action** — a named basketball concept (name, slug, aliases, category, difficulty, written breakdown, related Synergy play types).
- **Example** — a film example of an action (title, YouTube video ID, start/end seconds, note), rendered as a trimmed embed.
- **Player** — a thin player record (name, team, NBA API id) to be expanded when stats features are built.

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

# apply migrations and create an admin user
python manage.py migrate
python manage.py createsuperuser

# run the development server
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/` for the library and `http://127.0.0.1:8000/admin/` to add content.

## Roadmap

Planned in rough order:

1. **Styling** — a clean, restrained visual design pass.
2. **Action variations** — model support for variations and counters of a base action (e.g. Pistol Keep, Pistol Step-Up) as their own linked entries.
3. **Player stats** — surface NBA Synergy play-type stats on player pages via a scheduled job that caches data into PostgreSQL.
4. **Player search** — let users find possessions by player and situation, powered by NBA play-by-play data.
5. **Film clip pipeline** — auto-source possession-length clips via the NBA `VideoEvents` endpoint, cached server-side.
6. **Play-style recommendation** — a diagnostic quiz that maps a user's answers to play-style axes and recommends relevant actions and players to study.

## A note on video

Court Vision indexes film; it does not host it. Film examples are embedded or deep-linked from their original sources. The planned clip pipeline links to official NBA-hosted possession clips rather than rehosting any footage.

## License

MIT — see [LICENSE](LICENSE).
