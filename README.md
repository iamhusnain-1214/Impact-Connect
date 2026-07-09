# ImpactConnect Pakistan

A discovery platform for verified NGOs across Pakistan — search and filter a growing directory of 100+ organizations, and ask **Rahnuma**, an AI guide, to match you with the right cause based on what you want to help with.

Built as a cross-department summer collaboration between ITU Lahore students: Economics & Data Sciences (batch '24) and Artificial Intelligence (batch '25).

## Features

- **NGO directory** — search and filter by category, city, and keyword, with pagination
- **Rahnuma AI assistant** — describe a cause in plain language ("I want to help flood victims") and get matched with relevant verified NGOs, powered by the Gemini API
- **Role-based accounts** — separate donor and admin dashboards, selected explicitly at login
- **Reviews & ratings** — donors can rate and review NGOs
- **Admin panel** — add, verify, edit, and remove NGO listings

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** MySQL, with connection pooling
- **Frontend:** Vanilla JS, Jinja2 templates, custom CSS
- **AI:** Google Gemini API (`gemini-2.5-flash-lite`)
- **Auth:** Session-based, bcrypt password hashing

## Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set up the database:
   ```bash
   mysql -u root -p < db/schema.sql
   mysql -u root -p impactconnect < db/add_perf_indexes.sql
   python -m db.seed_admin
   python -m db.seed_100_ngos
   python -m db.seed_reviews
   ```

3. Create a `.env` file in the project root (never committed — see `.gitignore`):
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=impactconnect
   FLASK_SECRET_KEY=change_this
   GEMINI_API_KEY=your_key_from_aistudio.google.com
   ```

4. Run the app:
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000`. Default admin login is set in `db/seed_admin.py`.

## Project Structure

```
app.py              # Flask routes
api/index.py         # Vercel serverless entrypoint (wraps app.py)
vercel.json          # Vercel build/routing config
config.py           # env-based configuration
db/                 # schema, connection pooling, seed scripts
models/             # NGO, User, Review, Admin, AI recommender
templates/          # Jinja2 pages
static/             # CSS + JS
```

## Deploying to Vercel

Vercel runs Python apps as serverless functions, not a persistent server -
there's no MySQL hosting built in, and no server process stays "on" between
requests. This repo is set up to handle that:

- `api/index.py` is the entrypoint Vercel's Python runtime calls
- `vercel.json` routes `/static/*` to static hosting and everything else to
  the Flask app
- `db/connection.py` builds its connection pool lazily, sized small
  (`DB_POOL_SIZE=3`), so it doesn't exhaust your database's connection
  limit when multiple function instances run in parallel

**1. Get a MySQL database Vercel's functions can actually reach.**
Your local MySQL install won't work since Vercel's servers can't see
`localhost` on your machine. Use a hosted MySQL that accepts remote
connections over TLS - PlanetScale, TiDB Cloud, or Aiven all have usable
free tiers. Run the schema and seed scripts against that remote database
the same way you did locally:
```bash
mysql -h <host> -u <user> -p <database> < db/schema.sql
mysql -h <host> -u <user> -p <database> < db/add_perf_indexes.sql
# then, with .env pointed at the remote DB:
python -m db.seed_admin
python -m db.seed_100_ngos
```

**2. Push this repo to GitHub** (already done, per your repo link).

**3. Import the repo in Vercel** (vercel.com -> Add New -> Project -> pick
the repo). Vercel will detect `vercel.json` automatically.

**4. Set Environment Variables** in Project Settings, using the same names
as `.env.example`: `FLASK_ENV=production`, `FLASK_SECRET_KEY` (a long
random string, not the dev default), `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, `DB_NAME`, `DB_USE_SSL=true`, `GEMINI_API_KEY`.

`FLASK_ENV=production` matters: `config.py` will deliberately refuse to
start if it's set to production but `FLASK_SECRET_KEY` is still the dev
default, rather than silently shipping a forgeable session key.

**5. Deploy.** Vercel builds `api/index.py` as the function and serves
`static/` directly. Visit the generated `*.vercel.app` URL - `/api/health`
is a fast way to confirm the deploy is actually running before testing the
full UI.
